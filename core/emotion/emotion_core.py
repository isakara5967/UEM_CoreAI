from .primitive import (
    CoreAffectSystem,
    ThreatSafetySystem,
    AttachmentSystem,
    NoveltySystem,
    PainComfortSystem,
)

from .personality import (
    PersonalityProfile,
    ChronicStressModel,
    ResilienceModel,
)

from .integration import (
    AffectiveStateIntegrator,
    ValenceArousalModel,
    EmotionPatternClassifier,
    EmotionRegulationController,
    EthmorEmotionBridge,
)


class EmotionCore:
    '''UEM duygusal çekirdeği - Event-aware version'''

    def __init__(self, event_bus=None):
        self.event_bus = event_bus
        
        # Primitive katman
        self.core_affect = CoreAffectSystem()
        self.threat_safety = ThreatSafetySystem()
        self.attachment = AttachmentSystem()
        self.novelty = NoveltySystem()
        self.pain_comfort = PainComfortSystem()

        # Personality & long-term katman
        self.personality_profile = PersonalityProfile()
        self.chronic_stress = ChronicStressModel()
        self.resilience = ResilienceModel()

        # Affect Integration & Regulation katmanı
        self.affective_state_integrator = AffectiveStateIntegrator()
        self.valence_arousal_model = ValenceArousalModel()
        self.emotion_pattern_classifier = EmotionPatternClassifier()
        self.emotion_regulation_controller = EmotionRegulationController()
        self.ethmor_emotion_bridge = EthmorEmotionBridge()

        self.initialized = True
        
        # Current emotional state (simple PAD model)
        self.valence = 0.0      # -1 (negative) to +1 (positive)
        self.arousal = 0.0      # -1 (calm) to +1 (excited)
        self.dominance = 0.0    # -1 (submissive) to +1 (dominant)

    def start(self):
        # Primitive katman başlığı
        print('   + Primitive Affect Systems')
        self.core_affect.start()
        self.threat_safety.start()
        self.attachment.start()
        self.novelty.start()
        self.pain_comfort.start()

        # Personality & long-term katman başlığı
        print('   + Personality & Long-Term Affective Structure')
        self.personality_profile.start()
        self.chronic_stress.start()
        self.resilience.start()

        # Affect Integration & Regulation katmanı başlığı
        print('   + Affect Integration & Regulation System')
        self.affective_state_integrator.start()
        self.valence_arousal_model.start()
        self.emotion_pattern_classifier.start()
        self.emotion_regulation_controller.start()
        self.ethmor_emotion_bridge.start()

    # Event handlers
    async def on_planning_action(self, event):
        '''Handle planning decisions and update emotional state'''
        from core.event_bus import Event, EventPriority
        
        action_name = event.data.get('action_name', 'UNKNOWN')
        action_params = event.data.get('action_params', {})
        
        # Update emotional state based on action type
        old_valence = self.valence
        old_arousal = self.arousal
        
        if action_name == 'ESCAPE':
            # Fear response: negative valence, high arousal
            danger_level = action_params.get('danger_level', 0.5)
            self.valence = max(-1.0, self.valence - danger_level * 0.3)
            self.arousal = min(1.0, self.arousal + danger_level * 0.5)
            self.dominance = max(-1.0, self.dominance - 0.2)
            
        elif action_name == 'APPROACH_TARGET':
            # Curiosity/interest: slightly positive, moderate arousal
            self.valence = min(1.0, self.valence + 0.1)
            self.arousal = min(1.0, self.arousal + 0.2)
            self.dominance = min(1.0, self.dominance + 0.1)
            
        elif action_name == 'EXPLORE':
            # Mild curiosity
            self.valence = min(1.0, self.valence + 0.05)
            self.arousal = min(1.0, self.arousal + 0.1)
        
        # Decay toward neutral (homeostasis)
        self.valence *= 0.95
        self.arousal *= 0.9
        self.dominance *= 0.95
        
        # Classify emotion
        emotion_label = self._classify_emotion()
        
        # Log state change
        print(f'[Emotion] Action: {action_name} → Valence: {self.valence:.2f}, '
              f'Arousal: {self.arousal:.2f}, Emotion: {emotion_label}')
        
        # Publish emotion state change event
        if self.event_bus and abs(self.valence - old_valence) > 0.05:
            emotion_event = Event(
                type='emotion.state_changed',
                source='emotion_core',
                data={
                    'valence': self.valence,
                    'arousal': self.arousal,
                    'dominance': self.dominance,
                    'emotion': emotion_label,
                    'trigger_action': action_name,
                },
                priority=EventPriority.NORMAL
            )
            await self.event_bus.publish(emotion_event)

    def _classify_emotion(self) -> str:
        '''Simple PAD-based emotion classification'''
        if self.valence > 0.3 and self.arousal > 0.3:
            return 'joy'
        elif self.valence < -0.3 and self.arousal > 0.3:
            if self.dominance < -0.2:
                return 'fear'
            else:
                return 'anger'
        elif self.valence < -0.3 and self.arousal < -0.2:
            return 'sadness'
        elif abs(self.valence) < 0.2 and abs(self.arousal) < 0.2:
            return 'neutral'
        elif self.arousal > 0.3:
            return 'excited'
        else:
            return 'calm'

    def get_state(self) -> dict:
        '''Return current emotional state'''
        return {
            'valence': self.valence,
            'arousal': self.arousal,
            'dominance': self.dominance,
            'emotion': self._classify_emotion(),
        }

    # =========================================================================
    # EVALUATE API (v1)
    # =========================================================================

    def evaluate(self, world_snapshot, state_vector) -> dict:
        """
        Appraisal hesaplamasını yapan resmi API (v1).
        
        Args:
            world_snapshot: WorldSnapshot veya dict (danger_level içermeli)
            state_vector: (resource, threat, wellbeing) tuple
            
        Returns:
            AppraisalResult benzeri dict
        """
        # Extract danger level
        danger = 0.0
        if hasattr(world_snapshot, 'environment_state'):
            danger = getattr(world_snapshot.environment_state, 'danger_level', 0.0)
        elif hasattr(world_snapshot, 'danger_level'):
            danger = world_snapshot.danger_level
        elif isinstance(world_snapshot, dict):
            danger = world_snapshot.get('danger_level', 0.0)
        
        # Extract health/resource from state_vector
        health = state_vector[0] if state_vector else 0.5
        
        # Compute PAD values
        valence = -danger * 0.5 + (health - 0.5) * 0.3
        valence = max(-1.0, min(1.0, valence))
        
        arousal = 0.5 + danger * 0.4
        arousal = max(0.0, min(1.0, arousal))
        
        dominance = (health - danger) * 0.3
        dominance = max(-1.0, min(1.0, dominance))
        
        # Update internal state
        self.valence = valence
        self.arousal = arousal
        self.dominance = dominance
        
        # Classify emotion
        emotion_label = self._classify_emotion()
        
        return {
            'valence': valence,
            'arousal': arousal,
            'dominance': dominance,
            'emotion_label': emotion_label,
        }
