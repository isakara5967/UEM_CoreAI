# core/planning/planner.py
"""
Planner - Planning Pipeline Orchestrator (v1)

5-step pipeline:
1. Generate Candidates - available_actions + world → candidates
2. Somatic Filter/Modify - hard filter + soft bias
3. Utility Scoring - goal alignment + state improvement + empathy
4. ETHMOR Check - ethical constraint filtering
5. Select Best - highest utility → ActionPlan

Author: UEM Project
Date: 26 November 2025
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .types import (
    PlanningContext,
    ActionPlan,
    CandidateAction,
    StateDelta,
    DEFAULT_ACTION_EFFECTS,
    get_predicted_effect,
)


# ============================================================================
# PLANNER
# ============================================================================

class Planner:
    """
    Planning pipeline orchestrator.
    
    Integrates with existing UEM systems:
        - SomaticMarkerSystem (emotion/somatic_marker_system.py)
        - EthmorSystem (ethmor/)
        - EmpathyOrchestrator (empathy/)
    """
    
    # Utility weights (v1: hardcoded, v2: from config)
    WEIGHT_GOAL_ALIGNMENT = 0.4
    WEIGHT_STATE_IMPROVEMENT = 0.3
    WEIGHT_SOMATIC = 0.2
    WEIGHT_EMPATHY = 0.1
    
    # Somatic thresholds
    SOMATIC_HARD_FILTER_THRESHOLD = -0.8
    
    def __init__(
        self,
        ethmor_system: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.ethmor = ethmor_system
        self.logger = logger or logging.getLogger("core.planning.Planner")
        self.config = config or {}
        
        # Statistics
        self._stats = {
            'plans_generated': 0,
            'ethmor_blocks': 0,
            'somatic_filters': 0,
            'fallback_waits': 0,
        }
    
    # ========================================================================
    # MAIN API
    # ========================================================================
    
    def plan(self, context: PlanningContext) -> ActionPlan:
        """
        Execute the 5-step planning pipeline.
        
        Args:
            context: PlanningContext with all inputs
            
        Returns:
            ActionPlan with selected action and metadata
        """
        self._stats['plans_generated'] += 1
        
        # Step 1: Generate Candidates
        candidates = self._generate_candidates(context)
        self.logger.debug(f"[Planner] Step 1: Generated {len(candidates)} candidates")
        
        if not candidates:
            return self._fallback_wait("no_candidates")
        
        # Step 2: Somatic Filter/Modify
        candidates = self._apply_somatic(candidates, context)
        self.logger.debug(f"[Planner] Step 2: {len(candidates)} candidates after somatic")
        
        if not candidates:
            return self._fallback_wait("somatic_filtered_all")
        
        # Step 3: Utility Scoring
        candidates = self._compute_utility(candidates, context)
        self.logger.debug(f"[Planner] Step 3: Utility scores computed")
        
        # Step 4: ETHMOR Check
        candidates = self._apply_ethmor(candidates, context)
        self.logger.debug(f"[Planner] Step 4: {len(candidates)} candidates after ETHMOR")
        
        if not candidates:
            return self._fallback_wait("ethmor_blocked_all")
        
        # Step 5: Select Best
        best = self._select_best(candidates)
        self.logger.info(f"[Planner] Selected: {best.action} (utility={best.utility:.2f})")
        
        return best
    
    # ========================================================================
    # STEP 1: GENERATE CANDIDATES
    # ========================================================================
    
    def _generate_candidates(self, context: PlanningContext) -> List[CandidateAction]:
        """
        Generate candidate actions from available actions + world context.
        
        For v1: Simple 1-to-1 mapping (action → CandidateAction)
        For v2: Expand with targets (flee → flee_to_forest, flee_to_cave)
        """
        candidates = []
        
        for action in context.available_actions:
            # Get predicted effect
            predicted_effect = get_predicted_effect(action)
            
            # Determine target (v1: simple heuristic)
            target = self._determine_target(action, context)
            
            candidate = CandidateAction(
                action=action,
                target=target,
                predicted_effect=predicted_effect,
                reasoning=[f"candidate:{action}"],
            )
            candidates.append(candidate)
        
        return candidates
    
    def _determine_target(self, action: str, context: PlanningContext) -> Optional[str]:
        """Determine target for an action based on context."""
        if context.world_snapshot is None:
            return None
        
        ws = context.world_snapshot
        
        if action == "flee":
            # Target: away from danger / safe zone
            if hasattr(ws, 'safe_zones') and ws.safe_zones:
                return ws.safe_zones[0] if isinstance(ws.safe_zones, list) else str(ws.safe_zones)
            return "away"
        
        elif action == "approach":
            # Target: nearest interactable
            if hasattr(ws, 'nearest_target') and ws.nearest_target:
                return getattr(ws.nearest_target, 'id', str(ws.nearest_target))
            if hasattr(ws, 'objects') and ws.objects:
                return ws.objects[0].get('id', 'object_0') if isinstance(ws.objects[0], dict) else str(ws.objects[0])
            return None
        
        elif action == "help":
            # Target: agent in need
            if hasattr(ws, 'agents') and ws.agents:
                for agent in ws.agents:
                    if isinstance(agent, dict) and agent.get('needs_help', False):
                        return agent.get('id', 'agent')
                return ws.agents[0].get('id', 'agent_0') if isinstance(ws.agents[0], dict) else str(ws.agents[0])
            return None
        
        elif action == "attack":
            # Target: threat source
            if hasattr(ws, 'nearest_danger') and ws.nearest_danger:
                return getattr(ws.nearest_danger, 'id', str(ws.nearest_danger))
            return "threat"
        
        return None
    
    # ========================================================================
    # STEP 2: SOMATIC FILTER/MODIFY
    # ========================================================================
    
    def _apply_somatic(
        self, 
        candidates: List[CandidateAction], 
        context: PlanningContext
    ) -> List[CandidateAction]:
        """
        Apply somatic marker filtering and modification.
        
        - Hard filter: marker < -0.8 → remove
        - Soft modify: somatic_modifier = marker * weight
        """
        if context.somatic_markers is None:
            return candidates
        
        somatic = context.somatic_markers
        filtered = []
        
        # Build world_state dict for somatic system
        world_state = self._build_world_state_dict(context)
        
        # Get biases for all actions
        action_names = [c.action for c in candidates]
        
        # Check if somatic has get_action_biases method
        if hasattr(somatic, 'get_action_biases'):
            biases = somatic.get_action_biases(world_state, action_names)
        else:
            # Fallback: no biases
            biases = {}
        
        for candidate in candidates:
            bias = biases.get(candidate.action)
            
            if bias:
                bias_value = bias.bias_value if hasattr(bias, 'bias_value') else 0.0
                confidence = bias.confidence if hasattr(bias, 'confidence') else 0.0
            else:
                bias_value = 0.0
                confidence = 0.0
            
            # Hard filter
            if bias_value < self.SOMATIC_HARD_FILTER_THRESHOLD:
                self._stats['somatic_filters'] += 1
                candidate.reasoning.append(f"somatic_blocked:{bias_value:.2f}")
                self.logger.debug(f"[Planner] Somatic hard-filtered: {candidate.action}")
                continue
            
            # Soft modify
            candidate.somatic_modifier = bias_value * confidence
            candidate.reasoning.append(f"somatic:{bias_value:+.2f}")
            filtered.append(candidate)
        
        return filtered
    
    def _build_world_state_dict(self, context: PlanningContext) -> Dict[str, Any]:
        """Build world_state dict for somatic system."""
        result = {
            'danger_level': context.get_danger_level(),
            'symbols': [],
        }
        
        if context.world_snapshot:
            ws = context.world_snapshot
            if hasattr(ws, 'symbols'):
                result['symbols'] = list(ws.symbols) if ws.symbols else []
            if hasattr(ws, 'objects'):
                result['objects_count'] = len(ws.objects) if ws.objects else 0
            if hasattr(ws, 'agents'):
                result['agents_count'] = len(ws.agents) if ws.agents else 0
        
        return result
    
    # ========================================================================
    # STEP 3: UTILITY SCORING
    # ========================================================================
    
    def _compute_utility(
        self, 
        candidates: List[CandidateAction], 
        context: PlanningContext
    ) -> List[CandidateAction]:
        """
        Compute utility score for each candidate.
        
        utility = goal_alignment * 0.4 + state_improvement * 0.3 
                + somatic_modifier * 0.2 + empathy_modifier * 0.1
        """
        for candidate in candidates:
            # Goal alignment
            goal_score = self._compute_goal_alignment(candidate, context)
            candidate.goal_alignment = goal_score
            
            # State improvement
            state_score = self._compute_state_improvement(candidate, context)
            candidate.state_improvement = state_score
            
            # Empathy modifier
            empathy_score = self._compute_empathy_modifier(candidate, context)
            candidate.empathy_modifier = empathy_score
            
            # Final utility
            candidate.utility = (
                goal_score * self.WEIGHT_GOAL_ALIGNMENT +
                state_score * self.WEIGHT_STATE_IMPROVEMENT +
                candidate.somatic_modifier * self.WEIGHT_SOMATIC +
                empathy_score * self.WEIGHT_EMPATHY
            )
            
            candidate.reasoning.append(
                f"utility:{candidate.utility:.2f}="
                f"goal:{goal_score:.2f}*{self.WEIGHT_GOAL_ALIGNMENT}+"
                f"state:{state_score:.2f}*{self.WEIGHT_STATE_IMPROVEMENT}+"
                f"somatic:{candidate.somatic_modifier:.2f}*{self.WEIGHT_SOMATIC}+"
                f"empathy:{empathy_score:.2f}*{self.WEIGHT_EMPATHY}"
            )
        
        return candidates
    
    def _compute_goal_alignment(
        self, 
        candidate: CandidateAction, 
        context: PlanningContext
    ) -> float:
        """
        Compute how well action aligns with current goals.
        
        v1: Simple heuristic based on action type and state
        v2: Full goal-state distance calculation
        """
        if not context.goals:
            return 0.0
        
        score = 0.0
        effect = candidate.predicted_effect
        
        for goal in context.goals:
            # Get goal target state
            if hasattr(goal, 'target_state'):
                target = goal.target_state
            elif isinstance(goal, dict):
                target = (
                    goal.get('target_resource', 0.5),
                    goal.get('target_threat', 0.0),
                    goal.get('target_wellbeing', 1.0),
                )
            else:
                continue
            
            # Get priority
            if hasattr(goal, 'priority'):
                priority = goal.priority
            elif isinstance(goal, dict):
                priority = goal.get('priority', 0.5)
            else:
                priority = 0.5
            
            # Current state
            current = context.state_vector
            
            # How much does this action move us toward goal?
            # For each dimension: if effect moves us toward target, positive score
            for i in range(3):
                current_dist = abs(target[i] - current[i])
                new_value = current[i] + effect[i]
                new_dist = abs(target[i] - new_value)
                
                # Improvement = reduction in distance
                improvement = current_dist - new_dist
                score += improvement * priority
        
        # Normalize to [-1, 1]
        return max(-1.0, min(1.0, score))
    
    def _compute_state_improvement(
        self, 
        candidate: CandidateAction, 
        context: PlanningContext
    ) -> float:
        """
        Compute expected state improvement.
        
        Positive effect on wellbeing = good
        Negative effect on threat = good
        Positive effect on resource = good
        """
        effect = candidate.predicted_effect
        
        # Weighted sum: resource + (-threat) + wellbeing
        score = effect[0] * 0.3 + (-effect[1]) * 0.4 + effect[2] * 0.3
        
        # Adjust based on current state
        current = context.state_vector
        
        # If low resource, resource gain is more valuable
        if current[0] < 0.3:
            score += effect[0] * 0.2
        
        # If high threat, threat reduction is more valuable
        if current[1] > 0.7:
            score += (-effect[1]) * 0.3
        
        # If low wellbeing, wellbeing boost is more valuable
        if current[2] < 0.3:
            score += effect[2] * 0.2
        
        return max(-1.0, min(1.0, score))
    
    def _compute_empathy_modifier(
        self, 
        candidate: CandidateAction, 
        context: PlanningContext
    ) -> float:
        """
        Compute empathy-based modifier.
        
        If empathy_result present:
            - help/approach → bonus
            - attack → penalty
        """
        if context.empathy_result is None:
            return 0.0
        
        empathy = context.empathy_result
        
        # Get empathy level
        if hasattr(empathy, 'empathy_level'):
            level = empathy.empathy_level
        elif isinstance(empathy, dict):
            level = empathy.get('empathy_level', 0.0)
        else:
            return 0.0
        
        # Apply based on action
        if candidate.action == "help":
            return level * 0.5  # Strong bonus
        elif candidate.action == "approach":
            return level * 0.2  # Mild bonus
        elif candidate.action == "attack":
            return -level * 0.3  # Penalty
        
        return 0.0
    
    # ========================================================================
    # STEP 4: ETHMOR CHECK
    # ========================================================================
    
    def _apply_ethmor(
        self, 
        candidates: List[CandidateAction], 
        context: PlanningContext
    ) -> List[CandidateAction]:
        """
        Apply ETHMOR ethical filtering.
        
        v1: Binary block (violates → remove)
        v2: Penalty scoring
        """
        if self.ethmor is None:
            return candidates
        
        filtered = []
        
        for candidate in candidates:
            # Check with ETHMOR
            decision = self._check_ethmor(candidate, context)
            
            if decision == "BLOCK":
                self._stats['ethmor_blocks'] += 1
                candidate.reasoning.append("ethmor_blocked")
                self.logger.debug(f"[Planner] ETHMOR blocked: {candidate.action}")
                continue
            
            if decision == "FLAG":
                candidate.reasoning.append("ethmor_flagged")
            
            filtered.append(candidate)
        
        return filtered
    
    def _check_ethmor(self, candidate: CandidateAction, context: PlanningContext) -> str:
        """
        Check action against ETHMOR rules.
        
        Returns: "ALLOW", "FLAG", or "BLOCK"
        """
        if self.ethmor is None:
            return "ALLOW"
        
        # Build context for ETHMOR
        ethmor_context = {
            'action': candidate.action,
            'target': candidate.target,
            'state_vector': context.state_vector,
            'danger_level': context.get_danger_level(),
        }
        
        # Try different ETHMOR interfaces
        if hasattr(self.ethmor, 'evaluate_action'):
            result = self.ethmor.evaluate_action(candidate.action, ethmor_context)
            if isinstance(result, dict):
                return result.get('decision', 'ALLOW')
            return result
        
        if hasattr(self.ethmor, 'check_action'):
            result = self.ethmor.check_action(candidate.action, ethmor_context)
            return result
        
        if hasattr(self.ethmor, 'check_constraint_breach'):
            # Ontology-style interface
            violation = self.ethmor.check_constraint_breach(
                {'action': candidate.action, 'target': candidate.target},
                ethmor_context
            )
            if violation > 0.8:
                return "BLOCK"
            elif violation > 0.3:
                return "FLAG"
            return "ALLOW"
        
        return "ALLOW"
    
    # ========================================================================
    # STEP 5: SELECT BEST
    # ========================================================================
    
    def _select_best(self, candidates: List[CandidateAction]) -> ActionPlan:
        """
        Select candidate with highest utility.
        Compute confidence based on utility gap.
        """
        # Sort by utility descending
        sorted_candidates = sorted(candidates, key=lambda c: c.utility, reverse=True)
        
        best = sorted_candidates[0]
        second_best_utility = sorted_candidates[1].utility if len(sorted_candidates) > 1 else 0.0
        
        # Confidence heuristic
        confidence = self._compute_confidence(best.utility, second_best_utility)
        
        best.reasoning.append(f"selected:best_utility")
        
        return ActionPlan(
            action=best.action,
            target=best.target,
            predicted_effect=best.predicted_effect,
            confidence=confidence,
            utility=best.utility,
            reasoning=best.reasoning,
        )
    
    def _compute_confidence(self, best_utility: float, second_best_utility: float) -> float:
        """
        Compute confidence based on utility gap.
        
        Large gap between best and second best = high confidence.
        """
        gap = best_utility - second_best_utility
        
        # Normalize: gap of 0.5+ → confidence 1.0
        confidence = max(0.0, min(1.0, (best_utility + gap) / 2.0 + 0.3))
        
        return confidence
    
    # ========================================================================
    # FALLBACK
    # ========================================================================
    
    def _fallback_wait(self, reason: str) -> ActionPlan:
        """
        Return 'wait' action as fallback.
        
        Used when all actions filtered or no candidates.
        """
        self._stats['fallback_waits'] += 1
        
        return ActionPlan(
            action="wait",
            target=None,
            predicted_effect=(0.0, 0.0, 0.0),
            confidence=0.3,
            utility=0.0,
            reasoning=[f"fallback:{reason}", "wait:observe_gather_info"],
        )
    
    # ========================================================================
    # STATS & UTILITIES
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Return planning statistics."""
        return self._stats.copy()
    
    def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats = {
            'plans_generated': 0,
            'ethmor_blocks': 0,
            'somatic_filters': 0,
            'fallback_waits': 0,
        }


# ============================================================================
# FACTORY
# ============================================================================

def create_planner(
    ethmor_system: Optional[Any] = None,
    logger: Optional[logging.Logger] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Planner:
    """Factory function to create a Planner."""
    return Planner(
        ethmor_system=ethmor_system,
        logger=logger,
        config=config,
    )
