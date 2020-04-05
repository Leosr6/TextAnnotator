from utils.Constants import *
from data.SentenceElements import Actor
from core.WordNetWrapper import WordNetWrapper


def can_be_person_pronoun(name):
    return False if name == IT else name in f_personPronouns


def has_frequency_attached(action):
    return action.f_preAdvMod in f_frequencyWords if action.f_preAdvMod else False


def is_action_resolution_determiner(name):
    return name in f_actionResolutionDeterminer


def is_RC_pronoun(name):
    return name in f_relativeClausePronouns


def can_be_object_pronoun(name):
    return name in f_inanimatePronouns


def is_unreal_actor(obj):
    return isinstance(obj, Actor) and obj.f_unreal


def get_third_person(name):
    base = WordNetWrapper.get_base_form(name)
    if base in f_weakVerbToThirdPerson:
        return f_weakVerbToThirdPerson[base]
    elif base.endswith("s") or base.endswith("x"):
        return base + "es"
    else:
        return base + "s"
