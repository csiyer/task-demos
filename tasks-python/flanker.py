"""Flanker Task - PsychoPy Implementation"""
from psychopy import visual, core, event, gui
import random, csv, os

# ===== PARAMETERS =====
N_TRIALS = 30
FIXATION_DURATION = 0.5 # seconds
FEEDBACK_DURATION = 0.3 # seconds
DATA_FILE = './_data/flanker.csv'
# ======================

# Get subject ID
dlg = gui.Dlg(title="Flanker Task")
dlg.addField('Subject ID:')
dlg.show()
if not dlg.OK:
    core.quit()
subject_id = dlg.data[0]

# Setup - do not edit
win = visual.Window([800, 600], color='white', units='height')
fixation = visual.TextStim(win, text='+', color='black', height=0.1)
stim = visual.TextStim(win, text='', color='black', height=0.15)
feedback_stim = visual.TextStim(win, text='', color='black', height=0.08)

# Define the stimuli into a list of dictionaries, 
# each dictionary has the stimulus, correct key, and trial type
flanker_stimuli = [
    {'text': '<<<<<', 'correct_key': 'left', 'type': 'congruent'},
    {'text': '>>>>>', 'correct_key': 'right', 'type': 'congruent'},
    {'text': '<<><<', 'correct_key': 'right', 'type': 'incongruent'},
    {'text': '>><>>', 'correct_key': 'left', 'type': 'incongruent'}
]

# Show instructions
instruction_text = """
    Flanker Task\n\n
    Use the LEFT and RIGHT arrow keys\n
    to indicate the direction of the CENTER arrow.\n\n
    Press ESC at any time to quit\n
    Press SPACE to begin"""
instructions = visual.TextStim(win, text=instruction_text, color='black', height=0.05, wrapWidth=1.5)
instructions.draw()
win.flip()
event.waitKeys(keyList=['space'])

# Loop over the trials
results = []
for trial in range(N_TRIALS):
    # Show fixation
    fixation.draw()
    win.flip()
    core.wait(FIXATION_DURATION)
    
    # Pick a random flanker
    trial_info = random.choice(flanker_stimuli)
    stim.text = trial_info['text']
    stim.draw()
    win.flip()
    
    # Get response
    clock = core.Clock()
    keys = event.waitKeys(keyList=['left', 'right', 'escape'], timeStamped=clock)
    
    if keys[0][0] == 'escape':
        break
    
    response_key = keys[0][0]
    rt = keys[0][1]
    correct = response_key == trial_info['correct_key']
    
    # Show feedback
    feedback_stim.text = 'Correct!' if correct else 'Wrong'
    feedback_stim.color = 'green' if correct else 'red'
    feedback_stim.draw()
    win.flip()
    core.wait(FEEDBACK_DURATION)
    
    results.append({
        'subject_id': subject_id,
        'trial': trial,
        'type': trial_info['type'],
        'stimulus': trial_info['text'],
        'response': response_key,
        'correct': int(correct),
        'rt': rt
    })

# Save results (append to shared file)
file_exists = os.path.isfile(DATA_FILE)
with open(DATA_FILE, 'a', newline='') as f:
    fieldnames = ['subject_id', 'trial', 'type', 'stimulus', 'response', 'correct', 'rt']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    if not file_exists:
        writer.writeheader()
    writer.writerows(results)

# End
end_text = visual.TextStim(win, text='Task complete!\n\nPress SPACE to exit', color='black', height=0.08)
end_text.draw()
win.flip()
event.waitKeys(keyList=['space'])
win.close()
core.quit()