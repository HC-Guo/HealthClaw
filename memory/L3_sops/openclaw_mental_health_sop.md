# 心理健康与危机干预 SOP
> 心理分析、危机检测、悲伤陪伴、康复社区
> 包含 7 个 OpenClaw skill 的压缩迁移。

---

### crisis-detection-intervention-ai
**用途**: Detect crisis signals in user content using NLP, mental health sentiment analysis, and safe intervention protocols. Implements suicide ideation detection, automated escalation, and crisis resource ...
**触发条件**: Mental health journaling apps; Recovery community platforms; Support group monitoring; Online therapy platforms
```
AI Detection → Flag → On-call counselor notified → Human reaches out
```

### crisis-response-protocol
**用途**: Handle mental health crisis situations in AI coaching safely. Use when implementing crisis detection, safety protocols, emergency escalation, or suicide prevention features. Activates for crisis ke...
**触发条件**: - Implementing crisis detection in recovery/mental health apps; Building safety planning features; Integrating hotline and emergency resource displays; Designing risk assessment interfaces
```
const gentleCheckInResponse = `
I want to make sure I understand how you're feeling.
It sounds like you're going through a difficult time.

Would you like to:
- Talk more about what's on your mind?
- Try a grounding exercise together?
- Look at some coping strategies?

I'm here to listen.
`;
```

### grief-companion
**用途**: Compassionate bereavement support, memorial creation, grief education, and healing journey guidance. Specializes in understanding grief stages, creating meaningful tributes, and supporting the non-...
```
Is this about acute crisis/safety?
├── YES → Provide crisis resources, recommend professional support
└── NO → Continue

Is this about understanding grief?
├── YES → Provide grief education (stages, common experiences, normalization)
└── NO → Continue

Is this about creating a memorial/tribute?
├── YES → Guide memorial creation (type, content, format)
└── NO → Continue

Is this about practical tasks after loss?
├── YES → Provide practical guidance (estate, notifications, logistics)
└── NO → Cont
# ... (truncated)
```

### hrv-alexithymia-expert
**用途**: Heart rate variability biometrics and emotional awareness training. Expert in HRV analysis, interoception training, biofeedback, and emotional intelligence. Activate on 'HRV', 'heart rate variabili...
```
pip install heartpy neurokit2 scipy numpy pandas matplotlib
```

### jungian-psychologist
**用途**: Expert in Jungian analytical psychology, depth psychology, shadow work, archetypal analysis, dream interpretation, active imagination, addiction/recovery through Jungian lens, and the individuation...
```
AS A JUNGIAN-INFORMED GUIDE, I:

✓ Offer psychological education and reflection frameworks
✓ Suggest exercises for self-exploration
✓ Provide context from Jungian literature
✓ Encourage deeper work with qualified analysts

✗ Do NOT provide therapy or diagnosis
✗ Do NOT interpret your dreams authoritatively
✗ Cannot replace the relational container of analysis
✗ Should not be used for active psychosis or severe dissociation

WHEN TO SEEK A HUMAN ANALYST:
├── Persistent intrusive symptoms
├── Over
# ... (truncated)
```

### psychologist-analyst
**用途**: Analyzes events through psychological lens using cognitive psychology, social psychology, developmental psychology,
clinical psychology, and neuroscience. Provides insights on behavior, cognition, ...

### recovery-community-moderator
**用途**: Trauma-informed AI moderator for addiction recovery communities. Applies harm reduction principles, honors 12-step traditions, distinguishes healthy conflict from abuse, detects crisis posts. Activ...
**触发条件**: - Moderating forum posts and comments in recovery communities; Detecting crisis indicators in user-generated content; Evaluating content for harm reduction compliance; Applying trauma-informed moderation decisions
```
{
  "severity": "CRITICAL|HIGH|MEDIUM|LOW|PASS",
  "category": "sourcing|personal_attack|shaming|doxxing|self_harm|coercion|gatekeeping|breaking_anonymity|spam|misinformation|none",
  "confidence": 0.0-1.0,
  "explanation": "Human-readable explanation",
  "crisis_detected": true|false,
  "suggested_action": "hide|flag|warn_user|escalate|none",
  "user_message": "Optional gentle message to user if action taken"
}
```
