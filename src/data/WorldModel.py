class WorldModel:

    f_actions = []
    f_actors = []
    f_resources = []
    f_flows = []
    f_lastFlowAdded = None

    def add_action(self, action):
        self.f_actions.push(action)

    def add_actor(self, actor):
        self.f_actors.push(actor)

    def add_resource(self, resource):
        self.f_resources.push(resource)
