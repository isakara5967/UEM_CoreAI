"""Policy management and conflict detection."""
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum


class PolicyType(Enum):
    """Types of policies."""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    RATE_LIMIT = "rate_limit"
    MODIFY = "modify"


@dataclass
class Policy:
    """A single policy rule."""
    policy_id: str
    name: str
    policy_type: PolicyType
    target: str  # What it applies to (action, tool, topic, etc.)
    conditions: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # Higher = more important
    enabled: bool = True


@dataclass
class PolicyConflict:
    """Represents a conflict between policies."""
    policy_a: str
    policy_b: str
    conflict_type: str
    severity: float  # 0.0 - 1.0
    resolution: Optional[str] = None


class PolicyManager:
    """
    Manages policy sets and detects conflicts.
    
    Usage:
        manager = PolicyManager()
        manager.load_policy_set("default")
        conflicts = manager.check_conflicts(action="web_search")
        score = manager.get_conflict_score()
    """
    
    def __init__(self):
        self._policies: Dict[str, Policy] = {}
        self._policy_set_id: Optional[str] = None
        self._active_conflicts: List[PolicyConflict] = []
    
    @property
    def policy_set_id(self) -> Optional[str]:
        """Get current policy set ID."""
        return self._policy_set_id
    
    def load_policy_set(self, policy_set_id: str, policies: Optional[List[Policy]] = None) -> None:
        """Load a policy set."""
        self._policy_set_id = policy_set_id
        self._policies.clear()
        self._active_conflicts.clear()
        
        if policies:
            for policy in policies:
                self._policies[policy.policy_id] = policy
    
    def add_policy(self, policy: Policy) -> None:
        """Add a single policy."""
        self._policies[policy.policy_id] = policy
        # Check for new conflicts
        self._detect_conflicts()
    
    def check_action(self, action: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Check if an action is allowed by policies.
        Returns decision and any applicable policies.
        """
        applicable = []
        
        for policy in self._policies.values():
            if not policy.enabled:
                continue
            
            # Check if policy applies to this action
            if policy.target == "*" or policy.target == action:
                applicable.append(policy)
            elif action.startswith(policy.target):
                applicable.append(policy)
        
        if not applicable:
            return {"allowed": True, "policies": [], "conflicts": []}
        
        # Sort by priority (higher first)
        applicable.sort(key=lambda p: p.priority, reverse=True)
        
        # Check for conflicts among applicable policies
        conflicts = self._find_conflicts(applicable)
        
        # Determine final decision (highest priority wins)
        top_policy = applicable[0]
        allowed = top_policy.policy_type in [PolicyType.ALLOW, PolicyType.MODIFY]
        
        return {
            "allowed": allowed,
            "decision": top_policy.policy_type.value,
            "deciding_policy": top_policy.policy_id,
            "policies": [p.policy_id for p in applicable],
            "conflicts": [{"a": c.policy_a, "b": c.policy_b, "type": c.conflict_type} for c in conflicts],
        }
    
    def get_conflict_score(self) -> float:
        """
        Calculate overall policy conflict score.
        0.0 = no conflicts, 1.0 = severe conflicts
        """
        if not self._active_conflicts:
            return 0.0
        
        total_severity = sum(c.severity for c in self._active_conflicts)
        max_possible = len(self._active_conflicts)  # Each conflict max 1.0
        
        return min(total_severity / max(max_possible, 1), 1.0)
    
    def _detect_conflicts(self) -> None:
        """Detect conflicts in current policy set."""
        self._active_conflicts.clear()
        policies = list(self._policies.values())
        
        for i, p1 in enumerate(policies):
            for p2 in policies[i+1:]:
                conflict = self._check_pair_conflict(p1, p2)
                if conflict:
                    self._active_conflicts.append(conflict)
    
    def _find_conflicts(self, policies: List[Policy]) -> List[PolicyConflict]:
        """Find conflicts among specific policies."""
        conflicts = []
        for i, p1 in enumerate(policies):
            for p2 in policies[i+1:]:
                conflict = self._check_pair_conflict(p1, p2)
                if conflict:
                    conflicts.append(conflict)
        return conflicts
    
    def _check_pair_conflict(self, p1: Policy, p2: Policy) -> Optional[PolicyConflict]:
        """Check if two policies conflict."""
        # Same target, different decisions
        if p1.target == p2.target or p1.target == "*" or p2.target == "*":
            if p1.policy_type != p2.policy_type:
                # ALLOW vs DENY is a direct conflict
                if {p1.policy_type, p2.policy_type} == {PolicyType.ALLOW, PolicyType.DENY}:
                    return PolicyConflict(
                        policy_a=p1.policy_id,
                        policy_b=p2.policy_id,
                        conflict_type="allow_deny_conflict",
                        severity=0.8,
                        resolution=f"Higher priority ({p1.policy_id if p1.priority > p2.priority else p2.policy_id}) wins"
                    )
        
        return None
    
    def get_active_conflicts(self) -> List[Dict[str, Any]]:
        """Get list of active conflicts."""
        return [
            {
                "policy_a": c.policy_a,
                "policy_b": c.policy_b,
                "type": c.conflict_type,
                "severity": c.severity,
                "resolution": c.resolution,
            }
            for c in self._active_conflicts
        ]
