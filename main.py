from . import construction, commandline, helpers, tablib, variables
from sap2000.constants import MATERIAL_TYPES, UNITS,STEEL_SUBTYPES, PLACEHOLDER
from colony import ReactiveSwarm
from structure import Structure
from time import strftime
import os, sys

class Simulation:
  def __init__(self):
    self.SapProgram = None
    self.SapModel = None
    self.Structure = None
    self.Swarm = None
    self.started = False

  def __setup_general(self):
    '''
    Function to setup the general settigns for the SAP2000 program
    '''
    # switch to default units HERE
    ret = self.SapModel.SetPresentUnits(UNITS[variables.program_units])
    if ret:
      return False

    # add load patterns HERE, which by default also defines a Load Case
    if not helpers.addloadpattern(self.SapModel, variables.robot_load_case, 
      'LTYPE_DEAD'):
      print ("Failure when adding the loadpattern {}".format(
        variables.robot_load_case))
      return False

    if not self.__setup_case(variables.robot_load_case):
      print ("Failure when setting-up load case {}.".format(
        variables.robot_load_case))
      return False
    if not self.__setup_case("DEAD"):
      print("Failure setting up DEAD case.")
      return False

    return True

  def __setup_case(self, name):
    # Initialize Non-linear
    ret = self.SapModel.LoadCases.StaticNonlinear.SetCase(name)
    if ret:
      return False
    # Set options (P-delta)
    ret = self.SapModel.LoadCases.StaticNonlinear.SetGeometricNonlinearity(name,
      1)
    if ret:
      return False

    # Set loads
    if name == "DEAD":
      ret,load_types,loads,scales = self.SapModel.LoadCases.StaticNonlinear.SetLoads(
        name,1,["Load"],[name],[1])
    else:
      ret,load_types,loads,scales = self.SapModel.LoadCases.StaticNonlinear.SetLoads(
        name,2,["Load","Load"],[name,"DEAD"],[1,1])

    if ret:
      return False

    return True

  def __setup_analysis(self):
    '''
    Funtion to set up the analysis model to the correct values
    '''
    # Set the degrees of Freedom
    DOF = (True,True,True,True,True,True)
    ret, DOF = self.SapModel.Analyze.SetActiveDOF(DOF)
    if ret:
      print("Failure with DOF.")
      return False

    # Set the cases to be analyzed (all cases)
    ret = self.SapModel.Analyze.SetRunCaseFlag("",True,True)
    if ret:
      print("Failure with run flag.")
      return False

    # Set Solver Options (Multithreaded, Auto, 64bit, robot_load_case)
    ret = self.SapModel.Analyze.SetSolverOption_1(2,0,False,
      variables.robot_load_case)
    if ret:
      print("Failure with sovler options")
      return False

    return True

  def __setup_material(self):
    '''
    Sets up our beam materials
    '''
    # Defining our Scaffold Tube Material Property
    ret, name = self.SapModel.PropMaterial.AddQuick(variables.material_property,
      MATERIAL_TYPES[variables.material_type],
      STEEL_SUBTYPES[variables.material_subtype],PLACEHOLDER,PLACEHOLDER,
      PLACEHOLDER,PLACEHOLDER,PLACEHOLDER,variables.material_property)
    if ret or name != variables.material_property:
      return False

    # Defining the Frame Section. This is the Scaffold Tube
    ret = self.SapModel.PropFrame.SetPipe(variables.frame_property_name,
      variables.material_property,variables.outside_diameter,
      variables.wall_thickness)
    if ret:
      return False

    return True

  def __push_information(self,file_obj):
    '''
    Writes out the data from variables and construction
    '''
    # Pull the names of all the variables and use that to get their attributes 
    # and store them in a list of names, values
    variables_text = 'variables', ([(constant, getattr(variables, constant)) for
     constant in dir(variables) if '__' not in constant and '.' not in constant])
    construction_text = 'construction', ([(constant, getattr(construction,
      constant)) for constant in dir(construction) if '__' not in constant 
      and '.' not in constant])
    
    # Cycle through both modules and store information the data
    data = ''
    for name, file_data in variables_text, construction_text:
      data += 'Data from the file {}.\n\n'.format(name)
      for var_name, value in file_data:
        data += var_name + ' : ' + str(value) + '\n'
      data += '\n\n'

    # Write out the data and you are now done
    file_obj.write(data)

  def __push_data(self,data,file_obj,i):
    '''
    Writes a set of data to a data file in specified format
    '''
    to_write = "Timestep: {}\n\n\n".format(str(i))
    for name, state in data.items():
      to_write += "{} = \n\n".format(name)
      for key, temp_data in state.items():
        to_write += "{} : {}\n".format(str(key),str(temp_data))
      to_write += "\n"
    file_obj.write(to_write + "\n")

  def __push_excel(self,data,file_obj,i):
    '''
    Writes a set of data to an excel file
    '''
    pass 

  def reset(self, comment = ""):
    '''
    Allows us to reset everything without exiting the SAP program
    '''
    if self.started:
      # Resetting the SAP Program (this saves the previous file)
      self.SapProgram.reset()

      # Creating new SAP Files
      outputfolder = ('C:\SAP 2000\\' +strftime("%b-%d") + "\\" + 
        strftime("%H_%M_%S") + comment + "\\")
      outputfilename = "tower.sdb"
      outputfile = outputfolder + outputfilename

      # Create a new blank moder
      ret = self.SapModel.File.NewBlank()
      assert ret == 0

      # Create directory if necessary
      path = os.path.dirname(outputfile)
      helpers.path_exists(path)

      # Save to the new file
      ret = self.SapModel.File.Save(outputfolder + outputfilename)
      assert ret == 0

      # Reset the structure and the swarm
      self.Structure.reset()
      self.Swarm.reset()

      return outputfolder

    else:
      print("The simulation is not started. Cannot reset.")

  def start(self, robots = 10, comment = ""):
    '''
    This starts up the SAP 2000 Program and hides it.
    '''
    if self.started:
      print("Simulation has already been started")
    else:
      outputfolder = ('C:\SAP 2000\\' +strftime("%b-%d") + "\\" + 
        strftime("%H_%M_%S") + comment + "\\")
      outputfilename = "tower.sdb"
      self.SapProgram, self.SapModel = commandline.run("",
        outputfolder + outputfilename)
      self.SapProgram.hide()
      self.started = True

    # Make python structure and start up the colony
    self.Structure = Structure()
    self.Swarm = ReactiveSwarm(robots, self.Structure, self.SapProgram)

    return outputfolder

  def stop(self):
    '''
    This stops the simulation gracefully
    '''
    if self.started:
      ret = self.SapProgram.exit()
      assert ret == 0
      self.started = False
    else:
      print("No simulation started. Use Simulation.Start() to begin.")

  def go(self,robots = 10, timesteps = 10, debug = True, comment = ""):
    '''
    Direct accesss
    '''
    outputfolder = ""
    if not self.started:
      outputfolder = self.start(robots=robots, comment=comment)
    self.run_simulation(timesteps,debug,comment,outputfolder)
    self.stop()

  def run_simulation(self,timesteps = 10, debug = True,comment = "",
    outputfolder=""):
    '''
    Runs the simulation according to the variables passed in.
    '''
    start_time = strftime("%H:%M:%S")
    # Make sure the simulation has been started. If not, exit.
    if not self.started:
      print("The simulation has not been started. Start it, then run it, or \
        simply Simulation.go()")
      sys.exit(1)

    # Make sure that the model is not locked so that we can change properties. 
    # Unlock it if it is
    if self.SapModel.GetModelIsLocked():
      self.SapModel.SetModelIsLocked(False)

    # Set everything up.
    if not self.__setup_general():
      sys.exit("General Setup Failed.")
    if not self.__setup_material():
      sys.exit("Material Setup Failed.")
    if not self.__setup_analysis():
      sys.exit("Analysis Setup Failed.")

    # Open files for writing if debugging
    with open(outputfolder + 'structure_excel.xls', 'w+') as struct_excel, open(outputfolder + 'robots.xls', 'w+') as robot_excel, open(outputfolder + "robot_data.txt", 'w+') as loc_text, open(outputfolder + "sap_failures.txt", 'w+') as sap_failures, open(outputfolder + "run_data.txt", 'w+') as run_text, open(outputfolder + "structure.txt", "w+") as struct_data:
      loc_text.write("This file contains information on the robots at each \
        timestep if debugging.\n\n")
      sap_failures.write("This file contains messages created when SAP 2000 does\
       not complete a function successfully if debugging.\n\n")
      struct_data.write("This file contains the data about the Pythonic \
        structure.\n\n")
      run_text.write("This file contains the variables used in the run of the \
        simulation.\n\nTotal timesteps: " + str(timesteps) + "\nStart time of \
        simumation: " + start_time + "\n\n")

      # Write variables
      self.__push_information(run_text)

      # Run the simulation!
      for i in range(timesteps):

        # Run the analysis if there is a structure to analyze and there are \
        # robots on it (ie, we actually need the information)
        if self.Structure.tubes > 0 and not self.Swarm.on_ground():
          # Save to a different filename every now and again
          if i % variables.analysis_timesteps == 0:
            filename = "tower-" + str(timesteps) + ".sdb"
            self.SapModel.File.Save(outputfolder + filename)

          ret = self.SapModel.Analyze.RunAnalysis()
          # When ret is not 0 debug is on, write out that it failed.
          if ret and debug:
            sap_failures.write("RunAnalysis failed! Value returned was \
              {}".format(str(ret)))

          # Deselect all outputs
          ret = self.SapModel.Results.Setup.DeselectAllCasesAndCombosForOutput()
          if ret and debug:
            sap_failures.write("Deselecting Cases failed! Value returned was \
              {}".format(str(ret)))

          # Select just the Robot Load Case for Output
          ret = self.SapModel.Results.Setup.SetCaseSelectedForOutput(
            variables.robot_load_case)

        # Make the decision based on analysis results
        self.Swarm.decide()

        # Make sure that the model has been unlocked, and if not, unlock it
        if self.SapModel.GetModelIsLocked():
          self.SapModel.SetModelIsLocked(False)

        # This section writes the robots decisions out to a file
        if debug:
          swarm_data = self.Swarm.get_information()
          beam_data = self.Structure.get_information()
          self.__push_excel(swarm_data,robot_excel,i+1)
          self.__push_excel(beam_data,struct_excel,i+1)
          self.__push_data(swarm_data,loc_text,i+1)
          self.__push_data(beam_data,struct_data,i+1)
          
        # Change the model based on decisions made (act on your decisions)
        self.Swarm.act()

        # Give a status update if necessary
        print("Finished timestep {}".format(str(i + 1)))

      # SIMULATION HAS ENDED (OUTSIDE OF FORLOOP)

      run_data = "\n\nStop time : " + strftime("%H:%M:%S") + "\n\n. Total beams\
       on structure: " + str(self.Structure.tubes) + "."
      run_data += "\n\n Maximum height of structure : " +  str(
        self.Structure.height) + "."

      run_text.write(run_data)