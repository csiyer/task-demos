"""Paired Associate Memory Task - PsychoPy Implementation"""
from psychopy import visual, core, event, gui
import random, os, csv, glob

# ===== PARAMETERS =====
N_PAIRS = 10
STUDY_TRIAL_DURATION = 3.0
FIXATION_DURATION = 0.5
FEEDBACK_DURATION = 1.5
STIMULI_FOLDER = '_stimuli'
STIMULI_TYPE = 'objects' # SCENES | FACES | OBJECTS
WORDS_FILE = 'words.txt'
DATA_FILE = './_data/paired_associate.csv'
# ======================

# Get subject ID
dlg = gui.Dlg(title="Paired Associates Task")
dlg.addField('Subject ID:')
dlg.show()
if not dlg.OK:
    core.quit()
subject_id = dlg.data[0]

# Setup
win = visual.Window([800, 600], color='white')
stim = visual.TextStim(win, text='', color='black', height=0.1)
fixation = visual.TextStim(win, text='+', color='black', height=0.1)

# Load stimuli and create pairs
# images
image_paths = glob.glob(f'{STIMULI_FOLDER}/{STIMULI_TYPE}/*.jpg')
random.shuffle(image_paths) 

# words
words_file = os.path.join(STIMULI_FOLDER, WORDS_FILE)
with open(words_file, 'r') as f:
    words = [line.strip().lower() for line in f if line.strip()]
random.shuffle(words)

# create pairs (image_path, word)
pairs = [(image_paths[i], words[i]) for i in range(N_PAIRS)]

# Instructions - Study
instruction_text = """
    Paired Associate Memory Task\n\n
    STUDY PHASE\n\n
    You will see an image paired with a word.\n
    Try to remember which image and word go together.\n\n
    Press ESC at any time to quit\n
    Press SPACE to begin"""
instructions = visual.TextStim(win, text= instruction_text, color='black', height=0.05, wrapWidth=1.5)
instructions.draw()
win.flip()
event.waitKeys(keyList=['space'])

# STUDY BLOCK
study_results = []
for trial, (cue, target) in enumerate(pairs):
    # Fixation
    fixation.draw()
    win.flip()
    core.wait(FIXATION_DURATION)
    
    # Show pair
    cue_stim = visual.ImageStim(win, image=cue, pos=(0, 0.2), size=0.4)
    cue_stim.draw()
    stim.text = target
    stim.pos = (0, -0.2)
    stim.draw()
    win.flip()
    core.wait(STUDY_TRIAL_DURATION)
    
    study_results.append({
        'subject_id': subject_id,
        'phase': 'study',
        'trial': trial,
        'cue': os.path.basename(cue),
        'target': target
    })

# Break
break_text = visual.TextStim(win, 
    text='End of study phase\n\nPress SPACE to continue to the test', 
    color='black', height=0.06)
break_text.draw()
win.flip()
event.waitKeys(keyList=['space'])

# Instructions - Test
instruction_text = """
    TEST PHASE\n\n
    You will see the image from each pair.\n
    Type the word it was paired with and press ENTER.\n\n
    Press ESC at any time to quit\n
    Press SPACE to begin"""
instructions.text = instruction_text
instructions.draw()
win.flip()
event.waitKeys(keyList=['space'])

# TEST BLOCK
test_results = []
test_pairs = pairs.copy()
random.shuffle(test_pairs)

for trial, (cue, correct_target) in enumerate(test_pairs):
    # Fixation
    fixation.draw()
    win.flip()
    core.wait(FIXATION_DURATION)
    
    # Show cue with prompt
    cue_stim = visual.ImageStim(win, image=cue, pos=(0, 0.2), size=0.4)
    response_text = visual.TextStim(win, text='', color='black', height=0.08, pos=(0, -0.2))
    
    # Get typed response
    response = ''
    clock = core.Clock()
    while True:
        cue_stim.draw()
        response_text.text = f'Your answer: {response}'
        response_text.draw()
        win.flip()
        
        keys = event.waitKeys()
        if keys[0] == 'return':
            break
        elif keys[0] == 'escape':
            win.close()
            core.quit()
        elif keys[0] == 'backspace':
            response = response[:-1]
        elif keys[0] == 'space':
            response += ' '
        elif len(keys[0]) == 1:
            response += keys[0]
    
    rt = clock.getTime()
    correct = response.strip().upper() == correct_target.upper()
    
    # Feedback
    feedback = visual.TextStim(win, 
        text=f'Correct: {correct_target}\nYour answer: {response}', 
        color='green' if correct else 'red', height=0.06)
    feedback.draw()
    win.flip()
    core.wait(FEEDBACK_DURATION)
    
    test_results.append({
        'subject_id': subject_id,
        'phase': 'test',
        'trial': trial,
        'cue': os.path.basename(cue),
        'target': correct_target,
        'response': response.strip(),
        'correct': int(correct),
        'rt': rt
    })

# Save results (append to shared file)
all_results = study_results + test_results
file_exists = os.path.isfile(DATA_FILE)
with open(DATA_FILE, 'a', newline='') as f:
    fieldnames = ['subject_id', 'phase', 'trial', 'cue', 'target', 'response', 'correct', 'rt']
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    if not file_exists:
        writer.writeheader()
    for row in all_results:
        # Fill missing fields with None
        for field in fieldnames:
            if field not in row:
                row[field] = None
        writer.writerow(row)

# End
end_text = visual.TextStim(win, text='Task complete!\n\nPress SPACE to exit', color='black', height=0.08)
end_text.draw()
win.flip()
event.waitKeys(keyList=['space'])
win.close()
core.quit()
