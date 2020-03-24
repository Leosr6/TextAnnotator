class WorldModel:

    f_actions = []
    f_actors = []
    f_resources = []
    f_flows = []
    f_lastFlowAdded = None

    def add_action(self, action):
        self.f_actions.append(action)

    def add_actor(self, actor):
        self.f_actors.append(actor)

    def add_resource(self, resource):
        self.f_resources.append(resource)

    def get_actions_of_sentence(self, stanford_sentence):
        pass

    def get_actors_of_sentence(self, stanford_sentence):
        pass

    def get_resources_of_sentence(self, stanford_sentence):
        pass

    def switch_actions(self, action, previous_action):
        pass
