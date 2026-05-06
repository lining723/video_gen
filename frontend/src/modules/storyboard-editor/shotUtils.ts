export function collectShotPayload(card) {
  return {
    sequence: Number(card.querySelector('[data-field="sequence"]').value),
    duration: Number(card.querySelector('[data-field="duration"]').value),
    shot_type: card.querySelector('[data-field="shot_type"]').value,
    camera_movement: card.querySelector('[data-field="camera_movement"]').value,
    scene_time: card.querySelector('[data-field="scene_time"]').value,
    background: card.querySelector('[data-field="background"]').value,
    sound_effects: card.querySelector('[data-field="sound_effects"]').value,
    action_direction: card.querySelector('[data-field="action_direction"]').value,
    description: card.querySelector('[data-field="description"]').value,
    subtitle_text: card.querySelector('[data-field="subtitle_text"]').value,
    dubbing_text: card.querySelector('[data-field="dubbing_text"]').value,
    voiceover_text: card.querySelector('[data-field="voiceover_text"]').value,
    voiceover_tone: card.querySelector('[data-field="voiceover_tone"]').value,
  };
}
