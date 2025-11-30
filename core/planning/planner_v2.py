# core/planning/planner_v2.py
"""
Planner v2 - Rebalanced Planning Pipeline

Changes from v1:
1. Softmax selection (scenario-based temperature)
2. Nonlinear repetition penalty
3. Effective risk (threat + health) for flee gating
4. Somatic scaling with learned confidence
5. Novelty bonus (exp decay)
6. Scenario-based planning weights

Consensus: Claude + Alice (27 November 2025)

Author: UEM Project
Date: 27 November 2025
"""

from __future__ import annotations

import logging
import math
import random
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

# Types from local module (for standalone testing)
# In production, use: from .types import ...
try:
    from .types import (
        PlanningContext,
        ActionPlan,
        CandidateAction,
        StateDelta,
        DEFAULT_ACTION_EFFECTS,
        get_predicted_effect,
    )
except ImportError:
    from planning_types import (
        PlanningContext,
        ActionPlan,
        CandidateAction,
        StateDelta,
        DEFAULT_ACTION_EFFECTS,
        get_predicted_effect,
    )


# ============================================================================
# RUN CONTEXT (Diagnostic Layer)
# ============================================================================

@dataclass
class RunContext:
    """
    Runtime context for tracking action statistics.
    
    Keeps Planner clean (SOLID principle - Alice recommendation).
    """
    action_stats: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    action_history: List[str] = field(default_factory=list)
    max_history: int = 100
    
    def record_action(self, action: str) -> None:
        """Record an action selection."""
        self.action_stats[action] += 1
        self.action_history.append(action)
        
        # Trim history if needed
        if len(self.action_history) > self.max_history:
            self.action_history = self.action_history[-self.max_history:]
    
    def get_distribution(self) -> Dict[str, float]:
        """Get action distribution as percentages."""
        total = sum(self.action_stats.values())
        if total == 0:
            return {}
        return {k: v / total for k, v in self.action_stats.items()}
    
    def get_recent_count(self, action: str, window: int = 5) -> int:
        """Count action occurrences in recent history."""
        recent = self.action_history[-window:] if self.action_history else []
        return recent.count(action)
    
    def get_diversity_score(self) -> float:
        """
        Calculate action diversity (0-1).
        Higher = more diverse action selection.
        """
        if not self.action_stats:
            return 1.0
        
        total = sum(self.action_stats.values())
        if total == 0:
            return 1.0
        
        # Normalized entropy
        n_actions = len(self.action_stats)
        if n_actions <= 1:
            return 0.0
        
        entropy = 0.0
        for count in self.action_stats.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log(p)
        
        max_entropy = math.log(n_actions)
        return entropy / max_entropy if max_entropy > 0 else 0.0


# ============================================================================
# PLANNER V2
# ============================================================================

class PlannerV2:
    """
    Rebalanced Planning Pipeline.
    
    Key improvements:
    - Softmax selection instead of argmax
    - Nonlinear repetition penalty
    - Effective risk for flee gating
    - Novelty bonus for exploration
    - Learned confidence somatic scaling
    """
    
    # Default weights (overridden by scenario config)
    DEFAULT_WEIGHTS = {
        "safety": 0.4,
        "curiosity": 0.3,
        "empathy": 0.3,
    }
    
    DEFAULT_TEMPERATURE = 0.5
    
    # Somatic thresholds
    SOMATIC_HARD_FILTER_THRESHOLD = -0.8
    
    def __init__(
        self,
        ethmor_system: Optional[Any] = None,
        somatic_system: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.ethmor = ethmor_system
        self.somatic = somatic_system
        self.logger = logger or logging.getLogger("core.planning.PlannerV2")
        self.config = config or {}
        
        # Run context for diagnostics
        self.run_context = RunContext()
        
        # Planning weights from config
        self.weights = self.config.get("planning_weights", self.DEFAULT_WEIGHTS)
        self.temperature = self.config.get("softmax_temperature", self.DEFAULT_TEMPERATURE)
        
        # Statistics
        self._stats = {
            'plans_generated': 0,
            'ethmor_blocks': 0,
            'somatic_filters': 0,
            'fallback_waits': 0,
            'softmax_selections': 0,
        }
    
    # ========================================================================
    # CONFIGURATION
    # ========================================================================
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """Update planner configuration (e.g., from scenario)."""
        if "planning_weights" in config:
            self.weights = config["planning_weights"]
            self.logger.info(f"[PlannerV2] Updated weights: {self.weights}")
        
        if "softmax_temperature" in config:
            self.temperature = config["softmax_temperature"]
            self.logger.info(f"[PlannerV2] Updated temperature: {self.temperature}")
    
    # ========================================================================
    # MAIN API
    # ========================================================================
    
    def plan(self, context: PlanningContext) -> ActionPlan:
        """
        Execute the rebalanced planning pipeline.
        
        Steps:
        1. Generate Candidates
        2. Apply Somatic (with learned confidence scaling)
        3. Compute Utility (with scenario weights + novelty bonus)
        4. Apply Repetition Penalty
        5. Apply Flee Gating (effective risk)
        6. ETHMOR Filter
        7. Softmax Selection
        """
        self._stats['plans_generated'] += 1
        
        # Step 1: Generate Candidates
        candidates = self._generate_candidates(context)
        self.logger.debug(f"[PlannerV2] Step 1: Generated {len(candidates)} candidates")
        
        if not candidates:
            return self._fallback_wait("no_candidates")
        
        # Step 2: Somatic Filter/Modify (with learned confidence)
        candidates = self._apply_somatic(candidates, context)
        self.logger.debug(f"[PlannerV2] Step 2: {len(candidates)} after somatic")
        
        if not candidates:
            return self._fallback_wait("somatic_filtered_all")
        
        # Step 3: Utility Scoring (with scenario weights + novelty)
        candidates = self._compute_utility(candidates, context)
        self.logger.debug(f"[PlannerV2] Step 3: Utility computed")
        
        # Step 4: Repetition Penalty (nonlinear)
        candidates = self._apply_repetition_penalty(candidates)
        self.logger.debug(f"[PlannerV2] Step 4: Repetition penalty applied")
        
        # Step 5: Flee Gating (effective risk)
        candidates = self._apply_flee_gating(candidates, context)
        self.logger.debug(f"[PlannerV2] Step 5: Flee gating applied")
        
        # Step 6: ETHMOR Check
        candidates = self._apply_ethmor(candidates, context)
        self.logger.debug(f"[PlannerV2] Step 6: {len(candidates)} after ETHMOR")
        
        if not candidates:
            return self._fallback_wait("ethmor_blocked_all")
        
        # Step 7: Softmax Selection
        best = self._softmax_select(candidates)
        
        # Record action
        self.run_context.record_action(best.action)
        
        self.logger.info(
            f"[PlannerV2] Selected: {best.action} "
            f"(utility={best.utility:.2f}, T={self.temperature})"
        )
        
        return best
    
    # ========================================================================
    # STEP 1: GENERATE CANDIDATES
    # ========================================================================
    
    def _generate_candidates(self, context: PlanningContext) -> List[CandidateAction]:
        """Generate candidate actions."""
        candidates = []
        
        for action in context.available_actions:
            predicted_effect = get_predicted_effect(action)
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
        """Determine target for an action."""
        if action == "flee" and context.world_snapshot:
            return "safe_direction"
        if action == "help" and context.empathy_result:
            if hasattr(context.empathy_result, 'target_agent_id'):
                return context.empathy_result.target_agent_id
        if action == "approach" and context.world_snapshot:
            ws = context.world_snapshot
            if hasattr(ws, 'nearest_object') and ws.nearest_object:
                return ws.nearest_object.get('id')
        return None
    
    # ========================================================================
    # STEP 2: SOMATIC (with learned confidence scaling)
    # ========================================================================
    
    def _apply_somatic(
        self,
        candidates: List[CandidateAction],
        context: PlanningContext,
    ) -> List[CandidateAction]:
        """
        Apply somatic markers with learned confidence scaling.
        
        Formula: somatic_scaled = raw * (0.4 + 0.6 * learned_confidence)
        """
        if not context.somatic_markers:
            return candidates
        
        filtered = []
        world_state = self._context_to_world_state(context)
        actions = [c.action for c in candidates]
        
        # Get biases from somatic system
        try:
            biases = context.somatic_markers.get_action_biases(world_state, actions)
        except Exception as e:
            self.logger.warning(f"[PlannerV2] Somatic bias error: {e}")
            return candidates
        
        for candidate in candidates:
            bias_info = biases.get(candidate.action)
            
            if bias_info:
                raw_bias = bias_info.bias_value
                # Use action experience confidence (learned)
                confidence = context.somatic_markers.get_confidence(candidate.action) if hasattr(context.somatic_markers, "get_confidence") else bias_info.confidence
                
                # Scale somatic by learned confidence
                # Formula: raw * (0.4 + 0.6 * confidence)
                scale = 0.4 + (0.6 * confidence)
                scaled_bias = raw_bias * scale
                
                # Hard filter
                if scaled_bias < self.SOMATIC_HARD_FILTER_THRESHOLD:
                    self.logger.debug(
                        f"[PlannerV2] Somatic filtered: {candidate.action} "
                        f"(bias={scaled_bias:.2f})"
                    )
                    self._stats['somatic_filters'] += 1
                    continue
                
                # Soft influence
                candidate.somatic_modifier = scaled_bias
                candidate.reasoning.append(
                    f"somatic:{scaled_bias:+.2f}(conf={confidence:.2f})"
                )
            
            filtered.append(candidate)
        
        return filtered
    
    # ========================================================================
    # STEP 3: UTILITY (with novelty bonus)
    # ========================================================================
    
    def _compute_utility(
        self,
        candidates: List[CandidateAction],
        context: PlanningContext,
    ) -> List[CandidateAction]:
        """
        Compute utility with:
        - Scenario-based weights
        - Novelty bonus (exp decay)
        """
        for candidate in candidates:
            # Base utility components
            goal_score = self._compute_goal_alignment(candidate, context)
            state_score = self._compute_state_improvement(candidate, context)
            empathy_score = self._compute_empathy_alignment(candidate, context)
            
            # Novelty bonus: 0.15 * exp(-count / 10)
            action_count = self.run_context.action_stats.get(candidate.action, 0)
            novelty_bonus = 0.15 * math.exp(-action_count / 10)
            
            # Weighted sum using scenario weights
            w_safety = self.weights.get("safety", 0.4)
            w_curiosity = self.weights.get("curiosity", 0.3)
            w_empathy = self.weights.get("empathy", 0.3)
            
            # Map scores to weights:
            # - safety → state_improvement (survival)
            # - curiosity → goal_alignment (exploration)
            # - empathy → empathy_alignment
            
            utility = (
                w_safety * state_score +
                w_curiosity * goal_score +
                w_empathy * empathy_score +
                candidate.somatic_modifier * 0.2 +
                novelty_bonus
            )
            
            candidate.utility = utility
            candidate.goal_alignment = goal_score
            candidate.state_improvement = state_score
            candidate.reasoning.append(
                f"utility:{utility:.2f}(g={goal_score:.2f},s={state_score:.2f},"
                f"e={empathy_score:.2f},n={novelty_bonus:.2f})"
            )
        
        return candidates
    
    def _compute_goal_alignment(
        self,
        candidate: CandidateAction,
        context: PlanningContext,
    ) -> float:
        """Compute goal alignment score."""
        if not context.goals:
            return 0.0
        
        total = 0.0
        weight_sum = 0.0
        
        effect = candidate.predicted_effect
        
        for goal in context.goals:
            priority = getattr(goal, 'priority', 0.5)
            target_state = getattr(goal, 'target_state', (0.5, 0.3, 0.7))
            
            # How much does this action move toward goal?
            current = context.state_vector
            
            # Effect brings us closer?
            delta_to_goal_before = sum(
                abs(t - c) for t, c in zip(target_state, current)
            )
            predicted_state = tuple(
                c + e for c, e in zip(current, effect)
            )
            delta_to_goal_after = sum(
                abs(t - p) for t, p in zip(target_state, predicted_state)
            )
            
            improvement = delta_to_goal_before - delta_to_goal_after
            total += improvement * priority
            weight_sum += priority
        
        return total / weight_sum if weight_sum > 0 else 0.0
    
    def _compute_state_improvement(
        self,
        candidate: CandidateAction,
        context: PlanningContext,
    ) -> float:
        """Compute state improvement score (survival focused)."""
        effect = candidate.predicted_effect
        resource_delta, threat_delta, wellbeing_delta = effect
        
        # Survival: reduce threat, maintain resources, improve wellbeing
        score = (
            -threat_delta * 1.5 +      # Threat reduction is good
            resource_delta * 0.8 +     # Resource gain is good
            wellbeing_delta * 0.5      # Wellbeing improvement is good
        )
        
        return score
    
    def _compute_empathy_alignment(
        self,
        candidate: CandidateAction,
        context: PlanningContext,
    ) -> float:
        """Compute empathy alignment score."""
        if not context.empathy_result:
            return 0.0
        
        empathy_level = getattr(context.empathy_result, 'empathy_level', 0.0)
        
        # Actions that help others
        if candidate.action == "help":
            return empathy_level * 1.5
        
        # Actions that harm others
        if candidate.action == "attack":
            return -empathy_level * 0.5
        
        return 0.0
    
    # ========================================================================
    # STEP 4: REPETITION PENALTY (nonlinear)
    # ========================================================================
    
    def _apply_repetition_penalty(
        self,
        candidates: List[CandidateAction],
    ) -> List[CandidateAction]:
        """
        Apply nonlinear repetition penalty.
        
        Formula: penalty = -(count²) * 0.05
        
        This breaks loops more aggressively than linear penalty.
        """
        for candidate in candidates:
            recent_count = self.run_context.get_recent_count(
                candidate.action, window=5
            )
            
            if recent_count > 0:
                # Nonlinear penalty: -(count²) * 0.05
                penalty = -(recent_count ** 2) * 0.05
                candidate.utility += penalty
                candidate.reasoning.append(f"repeat_penalty:{penalty:.2f}")
        
        return candidates
    
    # ========================================================================
    # STEP 5: FLEE GATING (effective risk)
    # ========================================================================
    
    def _apply_flee_gating(
        self,
        candidates: List[CandidateAction],
        context: PlanningContext,
    ) -> List[CandidateAction]:
        """
        Gate flee utility based on effective risk.
        
        Formula: effective_risk = 0.6 * threat + 0.4 * (1 - health)
        
        If risk < 0.2: flee_utility *= 0.5
        """
        # Get threat and health
        threat = 0.5
        health = 1.0
        
        if context.world_snapshot:
            ws = context.world_snapshot
            threat = getattr(ws, 'danger_level', 0.5)
            health = getattr(ws, 'player_health', 1.0)
        elif context.state_vector:
            # state_vector = (resource, threat, wellbeing)
            threat = context.state_vector[1]
            # 16D format: health at [3], fallback to [0] for legacy
            health = context.state_vector[3] if len(context.state_vector) > 3 else context.state_vector[0] if context.state_vector else 0.5
        
        # Effective risk = 0.6 * threat + 0.4 * (1 - health)
        effective_risk = (0.6 * threat) + (0.4 * (1 - health))
        
        for candidate in candidates:
            if candidate.action == "flee":
                original_utility = candidate.utility
                
                if effective_risk < 0.2:
                    # Low risk: significantly reduce flee attractiveness
                    candidate.utility *= 0.5
                    candidate.reasoning.append(
                        f"flee_gate:low_risk({effective_risk:.2f})"
                    )
                elif effective_risk < 0.4:
                    # Medium-low risk: slightly reduce
                    candidate.utility *= 0.8
                    candidate.reasoning.append(
                        f"flee_gate:med_risk({effective_risk:.2f})"
                    )
                # High risk: keep flee utility as is
        
        return candidates
    
    # ========================================================================
    # STEP 6: ETHMOR
    # ========================================================================
    
    def _apply_ethmor(
        self,
        candidates: List[CandidateAction],
        context: PlanningContext,
    ) -> List[CandidateAction]:
        """Apply ETHMOR ethical filtering."""
        if not self.ethmor:
            return candidates
        
        filtered = []
        
        for candidate in candidates:
            try:
                # Build ETHMOR context
                ethmor_context = self._build_ethmor_context(candidate, context)
                result = self.ethmor.evaluate(ethmor_context)
                
                decision = result.decision if hasattr(result, 'decision') else result
                
                if hasattr(decision, 'value'):
                    decision_str = decision.value
                else:
                    decision_str = str(decision)
                
                if decision_str == "BLOCK":
                    self.logger.debug(
                        f"[PlannerV2] ETHMOR blocked: {candidate.action}"
                    )
                    self._stats['ethmor_blocks'] += 1
                    continue
                
                if decision_str == "FLAG":
                    # Reduce utility but allow
                    candidate.utility *= 0.7
                    candidate.reasoning.append("ethmor:FLAG(-30%)")
                
                filtered.append(candidate)
                
            except Exception as e:
                self.logger.warning(
                    f"[PlannerV2] ETHMOR error for {candidate.action}: {e}"
                )
                filtered.append(candidate)
        
        return filtered
    
    def _build_ethmor_context(
        self,
        candidate: CandidateAction,
        context: PlanningContext,
    ) -> Any:
        """Build ETHMOR evaluation context."""
        try:
            from core.ethmor import EthmorContext
        except ImportError:
            # Fallback for standalone testing
            @dataclass
            class EthmorContext:
                RESOURCE_LEVEL: float = 0.5
                THREAT_LEVEL: float = 0.0
                WELLBEING: float = 0.5
                RESOURCE_LEVEL_before: float = 0.5
                THREAT_LEVEL_before: float = 0.0
                WELLBEING_before: float = 0.5
                RESOURCE_LEVEL_after: float = 0.5
                THREAT_LEVEL_after: float = 0.0
                WELLBEING_after: float = 0.5
                action_name: str = ""
        
        state = context.state_vector or (0.5, 0.5, 0.5)
        effect = candidate.predicted_effect
        
        return EthmorContext(
            RESOURCE_LEVEL=state[0],
            THREAT_LEVEL=state[1],
            WELLBEING=state[2],
            RESOURCE_LEVEL_before=state[0],
            THREAT_LEVEL_before=state[1],
            WELLBEING_before=state[2],
            RESOURCE_LEVEL_after=state[0] + effect[0],
            THREAT_LEVEL_after=state[1] + effect[1],
            WELLBEING_after=state[2] + effect[2],
            action_name=candidate.action,
        )
    
    # ========================================================================
    # STEP 7: SOFTMAX SELECTION
    # ========================================================================
    
    def _softmax_select(self, candidates: List[CandidateAction]) -> ActionPlan:
        """
        Select action using softmax distribution.
        
        p(a) = exp(U(a) / T) / Σ exp(U / T)
        
        Temperature from scenario config.
        """
        self._stats['softmax_selections'] += 1
        
        if len(candidates) == 1:
            return self._candidate_to_plan(candidates[0])
        
        # Compute softmax probabilities
        utilities = [c.utility for c in candidates]
        T = max(0.01, self.temperature)  # Prevent division by zero
        
        # Numerical stability: subtract max
        max_u = max(utilities)
        exp_utilities = [math.exp((u - max_u) / T) for u in utilities]
        sum_exp = sum(exp_utilities)
        
        probabilities = [e / sum_exp for e in exp_utilities]
        
        # Sample from distribution
        r = random.random()
        cumulative = 0.0
        selected_idx = 0
        
        for i, p in enumerate(probabilities):
            cumulative += p
            if r <= cumulative:
                selected_idx = i
                break
        
        selected = candidates[selected_idx]
        selected.reasoning.append(
            f"softmax:p={probabilities[selected_idx]:.2f},T={T}"
        )
        
        # Compute confidence
        confidence = self._compute_confidence(
            selected.utility,
            utilities,
            probabilities[selected_idx],
        )
        
        return self._candidate_to_plan(selected, confidence)
    
    def _compute_confidence(
        self,
        selected_utility: float,
        all_utilities: List[float],
        selection_prob: float,
    ) -> float:
        """Compute confidence in selection."""
        if len(all_utilities) < 2:
            return 0.8
        
        sorted_u = sorted(all_utilities, reverse=True)
        gap = sorted_u[0] - sorted_u[1] if len(sorted_u) > 1 else 0
        
        # Confidence from gap + selection probability
        confidence = min(1.0, 0.3 + gap * 0.5 + selection_prob * 0.4)
        
        return confidence
    
    def _candidate_to_plan(
        self,
        candidate: CandidateAction,
        confidence: float = 0.5,
    ) -> ActionPlan:
        """Convert CandidateAction to ActionPlan."""
        return ActionPlan(
            action=candidate.action,
            target=candidate.target,
            predicted_effect=candidate.predicted_effect,
            confidence=confidence,
            utility=candidate.utility,
            reasoning=candidate.reasoning,
        )
    
    # ========================================================================
    # FALLBACK
    # ========================================================================
    
    def _fallback_wait(self, reason: str) -> ActionPlan:
        """Return 'wait' action as fallback."""
        self._stats['fallback_waits'] += 1
        self.run_context.record_action("wait")
        
        return ActionPlan(
            action="wait",
            target=None,
            predicted_effect=(0.0, 0.0, 0.0),
            confidence=0.3,
            utility=0.0,
            reasoning=[f"fallback:{reason}", "wait:observe_gather_info"],
        )
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    def _context_to_world_state(self, context: PlanningContext) -> Dict[str, Any]:
        """Convert PlanningContext to world_state dict for somatic."""
        ws = {}
        
        if context.world_snapshot:
            snap = context.world_snapshot
            ws['danger_level'] = getattr(snap, 'danger_level', 0.5)
            ws['symbols'] = getattr(snap, 'symbols', [])
        
        if context.state_vector:
            ws['state_vector'] = context.state_vector
        
        return ws
    
    def get_stats(self) -> Dict[str, Any]:
        """Return planning statistics."""
        stats = self._stats.copy()
        stats['action_distribution'] = self.run_context.get_distribution()
        stats['diversity_score'] = self.run_context.get_diversity_score()
        return stats
    
    def get_action_distribution(self) -> Dict[str, float]:
        """Get action distribution for diagnostics."""
        return self.run_context.get_distribution()
    
    def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats = {
            'plans_generated': 0,
            'ethmor_blocks': 0,
            'somatic_filters': 0,
            'fallback_waits': 0,
            'softmax_selections': 0,
        }
        self.run_context = RunContext()


# ============================================================================
# FACTORY
# ============================================================================

def create_planner_v2(
    ethmor_system: Optional[Any] = None,
    somatic_system: Optional[Any] = None,
    logger: Optional[logging.Logger] = None,
    config: Optional[Dict[str, Any]] = None,
) -> PlannerV2:
    """Factory function to create a PlannerV2."""
    return PlannerV2(
        ethmor_system=ethmor_system,
        somatic_system=somatic_system,
        logger=logger,
        config=config,
    )
