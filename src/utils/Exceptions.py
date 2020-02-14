class PipeRequiredException(BaseException):
    def __init__(self, pipe):
        super("Pipe {} is required, but was not found".format(pipe))