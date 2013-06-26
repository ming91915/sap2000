from robots import Movable
import helpers, construction, variables

class Worker(Movable):
  def __init__(self,structure,location,program):
    super(Worker,self).__init__(structure,location,program)
    self.num_beams = variables.beam_capacity
    self.upwards = False

  def __pickup_beams(num = variables.beam_capacity):
    self.num_beam = self.num_beams + num
    self.weight = self.weight + variables.beam_load * num

  def __discard_beams(num = 1):
    self.num_beam = self.num_beam - num
    self.weight = self.weight - variables.beam_load * num

  def do_action(self):
    '''
    Overwriting the do_action functionality in order to have the robot move up or downward
    (depending on whether he is carrying a beam or not), and making sure that he gets a chance
    to build part of the structure if the situation is suitable.
    '''
    # If we can't construct here, then move
    if not self.construct():
      super(Worker,self).do_action()

    # Otherwise crawl somewhere else
    else:
      self.build()

  def get_direction(directions):
    ''' 
    Figures out which direction to move in. This means that if the robot is carrying a beam,
    it wants to move upwards. If it is not, it wants to move downwards. So basically the direction
    is picked by filtering by the z-component
    '''
    def filter_dict(dirs, new_dirs, comp_f):
      '''
      Filters a dictinary, taking out all directions not in the correct z-direction
      '''
      for beam, vectors in info['directions'].items():
        for vector in vectors:
          # vector[2] = the z-component
          if comt_f(vector[2]):
            new_dirs[beam] = vector
      return new_dirs

    # Get all the possible directions, as normal
    info = self.get_directions_info()

    # Still have beams, so move upwards
    directions = {}
    if self.num_beams > 0 or self.upwards:
      directions = filter_dict(info['directions'], directions, (lambda z : z > 0))
    # No more beams, so move downwards
    else:
      directions = filter_dict(info['directions'], directions, (lambda z : z < 0))

    from random import choice

    # This will only occur if no direction changes our vertical height. If this is the case, get directions as before
    if directions == {} and not self.at_top:
      beam_name = choice(list(info['directions'].keys()))
      direction = choice(info['directions'][beam_name])
      self.at_top = True

    # Otherwise we do have a set of directions taking us in the right place, so randomly pick any of them
    else:
      beam_name = choice(list(diretions.keys()))
      direction = directions[beam_name]

    return {  'beam'      : info['box'][beam_name],
              'direction' : direction }

  def wander(self):
    '''    
    When a robot is not on a structure, it wanders. The wandering in the working class
    works as follows. The robot moves around randomly with the following restrictions:
      The robot moves towards the home location if it has no beams and 
        the home location is detected nearby.
      Otherwise, if it has beams for construction, it moves toward the base specified construction
      site. If it finds another beam nearby, it has a tendency to climb that beam instead.
    '''
    def at_home():
      return within(construction.home, construction.home_size, self.__location)

    # Check to see if robot is at home location and has no beams
    if at_home() and self.num_beams == 0 :
      self.__pickup_beams(variables.beam_capacity)

    # Check to see if robot should build based on steps taken
    # This has been removed
    '''
    if self.steps_to_construct == 0:
      self.build()
    '''

    # Find nearby beams to climb on
    result = self.ground()
    if result == None:
      direction = self.get_ground_direction()
      new_location = helpers.sum_vectors(self.__location,helpers.scale(self.__step, helpers.make_unit(direction)))
      self.__change_location_local(new_location)
      # self.steps_to_construct -= 1
    else:
      dist, close_beam, direction = result['distance'], result['beam'], result['direction']

      # If the beam is within steping distance, just jump on it
      if self.num_beams > 0 and dist <= self.__step:
        # Set the beam as the current one, and set the ground direction to None (so we walk randomly if we do get off the beam again)
        self.beam = close_beam
        self.__ground_direction = None

        # Then move on the beam
        self.move(direction, close_beam)

      # If we can "detect" a beam, change the ground direction to approach it
      elif self.num_beams > 0 and dist <= variables.local_radius:
        self.__ground_direction = direction
        new_location = helpers.sum_vectors(self.__location, helpers.scale(self.__step, helpers.make_unit(direction)))
        self.__change_location_local(new_location)
      else:
        direction = self.get_ground_direction()
        new_location = helpers.sum_vectors(self.__location,helpers.scale(self.__step, helpers.make_unit(direction)))
        self.__change_location_local(new_location)
        # self.steps_to_construct -= 1


  def addbeam(self,p1,p2):
    '''
    Adds the beam to the SAP program and to the Python Structure. Might have to add joints 
    for the intersections here in the future too.
    '''
    # Add to sap program
    name = self.__program.frame_objects.addbycoord(p1,p2)

    # Add to python structure
    return self.__structure.add_beam(p1,p2,name)

  def build(self):
    '''
    This functions sets down a beam. This means it "wiggles" it around in the air until
    it finds a connection (programatically, it just finds the connection which makes the smallest
    angle). Returns false if something went wrong, true otherwise.
    '''
    # This is the i-end of the beam being placed. We pivot about this
    pivot = self.__location

    # This is the j-end of the beam (if directly vertical)
    vertical_point = helpers.sum_vectors(self.__location,(0,0,variables.beam_length))

    # We place it here in order to have access to the pivot and to the vertical point
    def add_ratios(box,dictionary):
      '''
      Returns the 'verticality' that the beams in the box allow according to distance.
      It also calculates the ratio according to the intersection points of the beam
      with the sphere. 
      '''
      for name in box:
        beam = box[name]
        # Get the closest points between the vertical and the beam
        points = helpers.closest_points(beam.endpoints,(pivot,vertical_point))
        if points != None:
          # Endpoints
          e1,e2 = points
          # Let's do a sanity check. The shortest distance should have no change in z
          assert e1[2] == e2[2]
          # If we can actually reach the second point from vertical
          if helpers.distance(pivot,e2) <= variables.beam_length:
            # Distance between the two endpoints
            dist = helpers.distance(e1,e2)
            # Change in z from vertical to one of the two poitns (we already asserted their z value to be equal)
            delta_z = abs(e1[2] - vertical_point[2])
            ratio = dist / delta_z
            # Check to see if in the dictionary. If it is, associate point with ration
            if e2 in dictionary:
              assert(dictionary[e2] == ratio)
            else:
              dictionary[e2] = ratio

        # Get the points at which the beam intersects the sphere created by the vertical beam      
        sphere_points = helpers.sphere_intersection(beam.endpoints,pivot,variables.beam_length)
        if sphere_points != None:
          # Cycle through intersection points (really, should be two, though it is possible for it to be one, in
          # which case, we would have already taken care of this). Either way, we just cycle
          for point in sphere_points:
            # The point is higher above. This way the robot only ever builds up
            if point[2] >= pivot[2]:
              projection = helpers.correct(pivot,vertical_point,point)
              # Sanity check
              assert(projection[2] == point[2])

              dist = helpers.distance(projection,point)
              delta_z = abs(point[2] - vertical_point[2])
              ratio = dist / delta_z
              if point in dictionary:
                assert(dictionary[point] == ratio)
              else:
                dictionary[point] = ratio

      return dictionary

    # get all beams nearby (ie, all the beams in the current box and possible those further above)
    local_box = self.__structure.get_box(self.__location)
    top_box = self.__structure.get_box(vertical_point)

    # Ratios contains the ratio dist / delta_z where dist is the shortest distance from the vertical beam
    # segment to a beam nearby and delta_z is the z-component change from the pivot point to the intersection point
    # Here, we add to ratios those that arise from the intersection points of the beams with the sphere.
    # The dictionary is indexed by the point, and each point is associated with one ratio
    ratios = add_ratios(local_box,add_ratios(top_box,ratios))

    # No ratios found, so just build vertically
    default_endpoint = helpers.sum_vectors(pivot,helpers.scale(variables.beam_length,helpers.make_unit(construction.beam['vertical_dir_set'])))
    if ratios == {}:
      return self.addbeam(pivot,default_endpoint)

    import math
    point = min(ratios, key=ratios.get)

    # If the smallest ratio is larger than what we've specified as the limit, then build vertically
    if ratios[point] > math.tan(math.radians(construction.beam['angle_constraint'])):
      return self.addbeam(pivot,default_endpoint)

    # Calculate the actual endpoint of the beam (now that we now direction vector)
    unit_direction = helpers.make_unit(helpers.make_vector(pivot,point))
    endpoint = helpers.sum_vectors(pivot,helpers.scale(variables.beam_length,unit_direction))

    # Construct the beammm! :))))
    return self.addbeam(pivot,endpoint)

  def construct(self):
    '''
    Decides whether the local conditions dictate we should build (in which case)
    It returns the two points that should be connected, or we should continue moving 
    (in which case, it returns None)
    ''' 
    if self.at_top or helpers.distances(self.__location,construction.construction_location) <= construction.construction_radius:
      self.at_top = False
      return True
    else:
      return False