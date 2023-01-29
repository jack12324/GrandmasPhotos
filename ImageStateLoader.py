import json

from ImageState import ImageState


def load_image_states():
    states = {}
    with open('imageStates.txt', 'r') as fin:
        line = fin.readline()
        while line:
            state_dict = json.loads(line)
            state = ImageState(state_dict['rotated'], state_dict['converted'], state_dict['uploaded'])
            states[state_dict['path']] = state
            line = fin.readline()
    return states


def save_image_states(image_states):
    with open('imageStates.txt', 'w') as out:
        for image_state in image_states:
            state_dict = image_states[image_state].to_dict()
            state_dict['path'] = image_state
            out.write(json.dumps(state_dict) + "\n")
