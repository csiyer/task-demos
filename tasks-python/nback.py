"""N-back Task - PsychoPy Implementation"""
from psychopy import visual, core, event, gui
import random, csv, os

# ===== PARAMETERS =====
N_TRIALS = 30
FIXATION_DURATION = 0.5
STIM_DURATION = 1
ITI_DURATION = 0.5
TARGET_PROPORTION = 0.3
BACKGROUND_COLOR = 'white'
DATA_FILE = './nback_data.csv'
# Stimuli
letters = ['B', 'C', 'D', 'F', 'G', 'H', 'J', 'K']
# ======================


################################# ignore all code in here, just for psychopy logistics
# Get subject ID
dlg = gui.Dlg(title="N-back Task")
dlg.addField('Subject ID:')
dlg.addField('N (1, 2, or 3):')
dlg.show()
if not dlg.OK:
    core.quit()
subject_id = dlg.data[0]
n = int(dlg.data[1])

# Setup
win = visual.Window([800, 600], color=BACKGROUND_COLOR)
fixation = visual.TextStim(win, text='+', color='black', height=0.1)
stim = visual.TextStim(win, text='', color='black', height=0.2)
feedback = visual.TextStim(win, text='', color='black', height=0.06)
################################# 

# Display instructions
instruction_text = """
    N-back Task\n\n
    Press SPACE when the current letter matches\n
    the letter from """ + str(n) + """ position(s) back\n\n
    Press ESC at any time to quit\n
    Press SPACE to begin"""
instructions = visual.TextStim(win, text= instruction_text, color='black', height=0.05, wrapWidth=1.5)
instructions.draw()
win.flip()
event.waitKeys(keyList=['space'])


# Run trials
results = [] # we will store the data in this list as we go
sequence_of_letters = [] # keep track of which letters we're showing
for trial in range(N_TRIALS): 
    # this will "loop" over the 30 trials. This measn the code inside this loop will run 30 times.
    # On each time through the loop, the variable "trial" will be set to the number of the loop.
    # It'll start at 1 and end at 30.
    # So on the first loop, "trial" will be equal to 1, on the second to 2, on the third to 2, and so on.
    # On each loop, we will determine what stimulus to show, and then display the trial. 
    # Then, we will measure the response, save the data, and move on to the next trial. 
    
    # First, we have to decide what stimulus to show--a "target" or non-target
    # this code will use a random number generator to make 30% of the trials "target" trials
    # Don't worry how this section works; it's a little complicated. All you need to know is that
    # once it runs, "current_letter" will contain the letter we need to display on this trial.
    if trial >= n and random.random() < TARGET_PROPORTION:
        is_target = True
        # target trial
        current_letter = sequence_of_letters[trial - n] # show the letter from n trials ago
    else:
        is_target = False
        # show a different letter -- don't worry 
        if trial >= n:
            current_letter = random.choice([l for l in letters if l != sequence_of_letters[trial - n]])
        else:
            current_letter = random.choice(letters)
    sequence_of_letters.append(current_letter)
    
    # Display the fixation cross at the start of the trial
    fixation.draw()
    win.flip()
    core.wait(FIXATION_DURATION)
    
    # Display the chosen letter
    stim.text = current_letter
    stim.draw()
    win.flip()
    
    # Get participant's response
    clock = core.Clock()
    keys = event.waitKeys(maxWait=STIM_DURATION, keyList=['space', 'escape'], timeStamped=clock)
    # if they click Escape, exit the experiment
    if keys and keys[0][0] == 'escape':
        break
    
    # if a response is made, compute whether it is correct
    if keys is not None and keys[0][0] == 'space': # space bar was pressed,
        correct = is_target # correct should be TRUE if is_target is TRUE and FALSE if is_target is FALSE 
        rt = keys[0][1] if keys else None # response time is stored in "keys" by the PsychoPy code above
    else: # space bar not pressed, this is correct if trial is non-target trial
        correct = not is_target # correct should be TRUE if is_target is FALSE and FALSE if is_target is TRUE 
        rt = None 
    
    # data to save from this trial
    results.append({
        'subject_id': subject_id,
        'n': n,
        'trial': trial,
        'stimulus': sequence_of_letters[trial],
        'is_target': int(is_target),
        'correct': int(correct),
        'rt': rt
    })
    
    # Brief inter-trial interval
    core.wait(ITI_DURATION)

# Save the data
file_exists = os.path.isfile(DATA_FILE)
with open(DATA_FILE, 'a', newline='') as f:
    fieldnames = ['subject_id', 'n', 'trial', 'stimulus', 'is_target', 'correct', 'rt']
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