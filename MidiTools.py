import midi
import copy

# creates and returns a midi track with the given chord progression
def create_chord_progression(progression, loops, res):
    # instantiate midi track
    track = midi.Track()

    # for each loop of chord progression
    for loop in range(loops):
        # for each chord in progression
        for (root,type,length,repeats) in progression:
            # get third and fifth notes
            third = 0
            fifth = root + 7
            if type == 'major':
                third = root + 4
            elif type == 'minor':
                third = root + 3

            # for each chord repetition
            for i in range(repeats):
                # instatiate midi notes and append to track
                on = midi.NoteOnEvent(tick=0, velocity=80, pitch=root)
                on3 = midi.NoteOnEvent(tick=0, velocity=80, pitch=third)
                on5 = midi.NoteOnEvent(tick=0, velocity=80, pitch=fifth)
                on8 = midi.NoteOnEvent(tick=0, velocity=80, pitch=root+12)
                track.append(on)
                track.append(on3)
                track.append(on5)
                track.append(on8)
                # instantiate midi off events and append to track
                off = midi.NoteOffEvent(tick=length*res, pitch=root)
                off3 = midi.NoteOffEvent(tick=0, pitch=third)
                off5 = midi.NoteOffEvent(tick=0, pitch=fifth)
                off8 = midi.NoteOffEvent(tick=0, pitch=root+12)
                track.append(off)
                track.append(off3)
                track.append(off5)
                track.append(off8)

    return track


# takes in a midi track object and returns a list of "steps", where each
# step is a list of midi events
def split_track(t,res):
    steps = []
    cur_step = []
    for event in t:
        if event.tick == 0:
            cur_step.append(event)
        else:
            steps.append(cur_step)
            for i in range((event.tick/res)-1):
                steps.append([])
            cur_step = [event]

    return steps


# takes in a midi track object and return a list of steps, where each
# step is a list of notes that are present in that step
def get_notes_per_step(t,res):
    # split track events into steps
    track_s = split_track(t,res)
    steps = []
    notes = []
    for step in track_s:
        for event in step:
            note = event.data[0]
            # check if event is a "note off" event
            is_off_event = (event.data[1] == 0)
            # check if note is already being played
            note_exists = (note in notes)
            # delete note if off event and note already being played
            if is_off_event and note_exists:
                notes.remove(note)
            # add note if not off event and note not already being played
            elif (not is_off_event) and (not note_exists):
                notes.append(note)

        # append list of notes to result
        steps.append(copy.deepcopy(notes))

    # get rid of empty steps at end of track
    for i in reversed(range(len(steps) - 1)):
        if len(steps[i]) == 0:
            steps.pop(i)

    return steps


# creates a midi track from a list of notes per step
def create_track_from_notes(notes, res):
    track = midi.Track()
    prev_note = notes[0]

    # append first note
    on = midi.NoteOnEvent(tick=0, velocity=80, pitch=notes[0])
    track.append(on)
    delay = 0
    for note in notes[1:]:
        off = midi.NoteOffEvent(tick=res, pitch=prev_note)
        # rest
        if note == -1:
            delay += 1
        else:
            on = midi.NoteOnEvent(tick=res * delay, velocity=80, pitch=note)
            track.append(off)
            track.append(on)
            prev_note = note
            delay = 0

    return track