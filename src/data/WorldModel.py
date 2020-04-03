class WorldModel:

    def __init__(self):
        self.f_actions = []
        self.f_actors = []
        self.f_resources = []
        self.f_flows = []
        self.f_lastFlowAdded = None

    def get_actions_of_sentence(self, stanford_sentence):
        return [action for action in self.f_actions if action.f_sentence == stanford_sentence]

    def get_actors_of_sentence(self, stanford_sentence):
        return [actor for actor in self.f_actors if actor.f_sentence == stanford_sentence]

    def get_resources_of_sentence(self, stanford_sentence):
        return [resource for resource in self.f_resources if resource.f_sentence == stanford_sentence]

    def switch_actions(self, action, previous_action):
        index1, index2 = self.f_actions.index(action), self.f_actions.index(previous_action)
        self.f_actions[index1] = previous_action, self.f_actions[index2] = action
