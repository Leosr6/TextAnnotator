from data.SentenceElements import Actor


class WorldModel:

    def __init__(self):
        self.f_actions = []
        self.f_actors = []
        self.f_resources = []
        self.f_flows = []
        self.f_lastFlowAdded = None

    def add_action(self, action):
        self.f_actions.append(action)
        self.add_specifiers(action)
        if action.f_xcomp:
            self.add_specifiers(action.f_xcomp)

    def add_resource(self, resource):
        self.f_resources.append(resource)
        self.add_specifiers(resource)

    def add_actor(self, actor):
        self.f_actors.append(actor)
        self.add_specifiers(actor)

    def add_flow(self, flow):
        self.f_flows.append(flow)
        self.f_lastFlowAdded = flow

    def add_specifiers(self, element):
        for spec in element.f_specifiers:
            spec_object = spec.f_object
            if spec_object:
                if isinstance(spec_object, Actor):
                    self.add_actor(spec_object)
                else:
                    self.add_resource(spec_object)

    def get_actions_of_sentence(self, stanford_sentence):
        return [action for action in self.f_actions if action.f_sentence == stanford_sentence]

    def get_actors_of_sentence(self, stanford_sentence):
        return [actor for actor in self.f_actors if actor.f_sentence == stanford_sentence]

    def get_resources_of_sentence(self, stanford_sentence):
        return [resource for resource in self.f_resources if resource.f_sentence == stanford_sentence]

    def switch_actions(self, action, previous_action):
        index1, index2 = self.f_actions.index(action), self.f_actions.index(previous_action)
        self.f_actions[index1] = previous_action, self.f_actions[index2] = action
