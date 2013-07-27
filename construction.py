import variables

# Home location
home = (variables.dim_x / 2.2, variables.dim_y / 2.2,0)
home_size = (36, 36, variables.epsilon)

# Location where construction is to begin
construction_location = (variables.dim_x / 2, variables.dim_y / 2,0)
construction_size = (36,36,variables.epsilon)

# Angle Contraint : When wiggling, if no beam is found within this
# angle from the vertical, than the beam is laid at vertical_angle_set (
# which is just an angle, so no direction is actually specified)
# All angles are in degrees.
beam = {
  'length'                    : variables.beam_length,
  'min_angle_constraint'      : 20,
  'angle_constraint'          : 45,
  'max_angle_constraint'      : 70,
  'vertical_dir_set'          : (0,0,1),
  'joint_limit'               : variables.joint_limit,
  'beam_limit'                : 0.16,
  'horizontal_beam_limit'     : 4,
  'structure_check'           : variables.structure_check,
  'support_angle'             : 60,
  'support_angle_min'         : 15,
  'support_angle_max'         : 75,

  # This is the angle from the vertical at which a beam is initially constructed
  'construction_angle'        : 20,

  # This is the angle between the beam we want to repair and the beam we are
  # currently on.
  # If the actual angle is greater, then we add a support beam
  # If it is less, then we repair directly
  'direct_repair_limit'      : 120,

  # This is how far a support beam construction from our current beam must
  # occur in order for the beam to be considered acceptable
  'support_angle_difference' : 10
}
