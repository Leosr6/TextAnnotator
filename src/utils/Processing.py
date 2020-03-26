from utils.Constants import *


def can_be_person_pronoun(name):
    value = name.lower()
    return False if value == IT else value in f_personPronouns


def has_frequency_attached(action):
    return action.f_preAdvMod.lower() in f_frequencyWords if action.f_preAdvMod else False


def is_action_resolution_determiner(name):
    return name.lower() in f_actionResolutionDeterminer


def is_RC_pronoun(name):
    return name.lower() in f_relativeClausePronouns


def can_be_object_pronoun(name):
    return name.lower() in f_inanimatePronouns
