package MarkerUser {
  private import ScalarValues::*;
  private import PysspCore::*;

  part def System :> SspModel {
    attribute fmu_meta : BallFmu;
  }

  port def BallParameters :> ParameterInterface {
    attribute g : Real;
  }

  attribute def BallFmu :> FmuMetadata {
    attribute source = "models/fmu/Ball/fmu";
    attribute implementation = "CoSimulation";
  }
}
