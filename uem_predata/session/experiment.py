"""Experiment and A/B bucket management."""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import random


@dataclass
class Experiment:
    """Experiment definition."""
    experiment_id: str
    name: str
    buckets: List[str]
    weights: Optional[List[float]] = None  # None = equal weights
    description: Optional[str] = None
    start_ts: Optional[datetime] = None
    end_ts: Optional[datetime] = None
    enabled: bool = True
    
    def __post_init__(self):
        if self.weights is None:
            self.weights = [1.0 / len(self.buckets)] * len(self.buckets)
        # Normalize weights
        total = sum(self.weights)
        self.weights = [w / total for w in self.weights]


@dataclass
class Assignment:
    """Bucket assignment for a user/session."""
    experiment_id: str
    bucket: str
    assigned_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class ExperimentManager:
    """
    Manages experiments and A/B bucket assignments.
    
    Usage:
        manager = ExperimentManager()
        manager.register_experiment(Experiment(
            experiment_id="exp_001",
            name="New Planner",
            buckets=["control", "treatment_a", "treatment_b"],
            weights=[0.5, 0.25, 0.25]
        ))
        bucket = manager.assign("exp_001", user_id="user_123")
    """
    
    def __init__(self, seed: Optional[int] = None):
        self._experiments: Dict[str, Experiment] = {}
        self._assignments: Dict[str, Assignment] = {}  # key: f"{exp_id}:{user_id}"
        self._random = random.Random(seed)
    
    def register_experiment(self, experiment: Experiment) -> None:
        """Register an experiment."""
        self._experiments[experiment.experiment_id] = experiment
    
    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get experiment by ID."""
        return self._experiments.get(experiment_id)
    
    def list_experiments(self, active_only: bool = True) -> List[Experiment]:
        """List all experiments."""
        experiments = list(self._experiments.values())
        
        if active_only:
            now = datetime.now(timezone.utc)
            experiments = [
                e for e in experiments
                if e.enabled
                and (e.start_ts is None or e.start_ts <= now)
                and (e.end_ts is None or e.end_ts >= now)
            ]
        
        return experiments
    
    def assign(
        self,
        experiment_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        force_bucket: Optional[str] = None
    ) -> Optional[str]:
        """
        Assign user/session to a bucket.
        Uses deterministic hashing for consistent assignment.
        """
        experiment = self._experiments.get(experiment_id)
        if not experiment or not experiment.enabled:
            return None
        
        # Check time bounds
        now = datetime.now(timezone.utc)
        if experiment.start_ts and experiment.start_ts > now:
            return None
        if experiment.end_ts and experiment.end_ts < now:
            return None
        
        # Create assignment key
        identity = user_id or session_id or str(self._random.random())
        assignment_key = f"{experiment_id}:{identity}"
        
        # Check existing assignment
        if assignment_key in self._assignments:
            return self._assignments[assignment_key].bucket
        
        # Force bucket if specified
        if force_bucket and force_bucket in experiment.buckets:
            bucket = force_bucket
        else:
            # Deterministic assignment using hash
            bucket = self._hash_assign(experiment, identity)
        
        # Store assignment
        self._assignments[assignment_key] = Assignment(
            experiment_id=experiment_id,
            bucket=bucket,
            user_id=user_id,
            session_id=session_id
        )
        
        return bucket
    
    def _hash_assign(self, experiment: Experiment, identity: str) -> str:
        """Deterministically assign bucket using hash."""
        hash_input = f"{experiment.experiment_id}:{identity}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        normalized = (hash_value % 10000) / 10000  # 0.0 - 1.0
        
        cumulative = 0.0
        for bucket, weight in zip(experiment.buckets, experiment.weights):
            cumulative += weight
            if normalized < cumulative:
                return bucket
        
        return experiment.buckets[-1]  # Fallback
    
    def get_assignment(
        self,
        experiment_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Optional[str]:
        """Get existing assignment without creating new one."""
        identity = user_id or session_id
        if not identity:
            return None
        
        assignment_key = f"{experiment_id}:{identity}"
        assignment = self._assignments.get(assignment_key)
        return assignment.bucket if assignment else None
    
    def get_all_assignments(self, user_id: str) -> Dict[str, str]:
        """Get all experiment assignments for a user."""
        result = {}
        for key, assignment in self._assignments.items():
            if assignment.user_id == user_id:
                result[assignment.experiment_id] = assignment.bucket
        return result
    
    def get_experiment_stats(self, experiment_id: str) -> Dict[str, Any]:
        """Get bucket distribution for an experiment."""
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            return {}
        
        bucket_counts = {b: 0 for b in experiment.buckets}
        
        for assignment in self._assignments.values():
            if assignment.experiment_id == experiment_id:
                bucket_counts[assignment.bucket] += 1
        
        total = sum(bucket_counts.values())
        
        return {
            "experiment_id": experiment_id,
            "name": experiment.name,
            "total_assignments": total,
            "bucket_counts": bucket_counts,
            "bucket_percentages": {
                b: (c / total * 100) if total > 0 else 0
                for b, c in bucket_counts.items()
            },
            "expected_weights": {
                b: w * 100
                for b, w in zip(experiment.buckets, experiment.weights)
            }
        }
    
    def clear_assignments(self, experiment_id: Optional[str] = None) -> int:
        """Clear assignments. Returns count cleared."""
        if experiment_id:
            to_remove = [
                k for k, v in self._assignments.items()
                if v.experiment_id == experiment_id
            ]
            for k in to_remove:
                del self._assignments[k]
            return len(to_remove)
        else:
            count = len(self._assignments)
            self._assignments.clear()
            return count
