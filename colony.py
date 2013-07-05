from worker import Worker
import construction

class Swarm:
  def __init__(self,size, structure, program):
    # The number of robots in the swarm
    self.size = size

    # The location of the swarm.
    self.home = (0,0,0)

    # Access to the structure, so we can create workers
    self.structure = structure

    # Access to the program
    self.model = program

    # create workers
    self.workers = {}
    for i in range(size):
      name = "worker_" + str(i)

      # workers start at home
      location = (i,0,0) 
      self.workers[name] = Worker(structure,location,program)

  def decide(self):
    # Assert that the model has been analyzed
    if not self.model.model.GetModelIsLocked():
      self.model.model.SetModelIsLocked(True)

    # Tell each robot to make the decion
    for worker in self.workers:
      self.workers[worker].decide()

  def act(self):
    # Asser that the model is not locked!
    if self.model.model.GetModelIsLocked():
      self.model.model.SetModelIsLocked(False)

    # Tell each robot to act
    for worker in self.workers:
      self.workers[worker].do_action()

  def get_information(self):
    information = {}
    for name, worker in self.workers.items():
      information[name] = worker.current_state()

    return information

class ReactiveSwarm(Swarm):
  def __init__(self,size,structure,program):
    super(ReactiveSwarm, self).__init__(size,structure,program)
    # Keeps track of how many robots we have created (in order to keep the 
    # names different)
    self.num_created = size
    self.original_size = size

  def reset(self):
    '''
    Create a spanking new army of workers the size of the original army!
    '''
    self.workers = {}
    for i in range(self.original_size):
      name = "worker_" + str(i)
      location = (i,0,0)
      self.workers[name] = Worker(self.structure,location,self.model)

  def on_ground(self):
    '''
    Returns whether or not all of the swarm is on the ground. If it is,
    no need to analyze the structure this time
    '''
    for worker in self.workers:
      if self.workers[worker].beam != None:
        return False

    return True

  def new_robots(self, num = 1):
    '''
    Creates new robots at the home location. They line up along the positive
    x-axis. The names are a continuation of the size of the swarm.
    '''
    for i in range(self.num_created, self.num_created + num):
      name = "worker_" + str(i)
      location = (i - num, 0, 0)
      self.workers[name] = Worker(self.structure,location,self.model)

    self.size += num
    self.num_created += num

  def delete_robot(self, name):
    '''
    Deletes the specified robot from the swarm if it exists
    '''
    if name in self.workers:
      self.workers[worker_name].change_location(construction.home, None)
      del(self.workers[worker_name])
      self.size -= 1
      return True
    else:
      return False

  def delete_random_robot(self):
    '''
    Deletes a random robot from the swarm.
    '''
    # Pick a random worker
    from random import choice
    worker_name = choice(self.workers.keys())

    return self.delete_robot(worker_name)

  def delete_random_robots(self,num = 1):
    '''
    Deletes the specified number of robots from the swarm. They are selected
    at random. Returns the number of robots successfully deleted.
    '''
    deleted = 0
    for i in range(num):
      if self.size > 0:
        if self.delete_random_robot():
          deleted += 1

    return deleted

  def delete_robots(self, names = []):
    '''
    Deletes the specified robots from the swarm (if found). If no name is passed
    in, it deletes nothing. Returns the number of robots successfully deleted.
    '''
    deleted = 0
    for name in names:
      if delete_robot(name):
        deleted += 1

    return deleted
