package PysspCore {
  part def SspModel;
  part def Analysis;
  part def FmuModel;

  port def ParameterInterface;

  attribute def ParameterSet;

  attribute def FmuMetadata {
    attribute source : String;
    attribute implementation : String;
  }

  attribute def SspMetadata {
    attribute source : String;
  }

  attribute def Experiment {
    attribute startTime : Real;
    attribute stopTime : Real;
    attribute stepSize : Real;
  }
}
