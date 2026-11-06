package Fmu {
  attribute def FmuMetadata {
    attribute source : String;
  }
  attribute def CompFmu :> FmuMetadata {
    attribute source = "build/fmus/Comp.fmu";
  }
  part def FmuModel;
  part def Comp :> FmuModel {
    attribute fmu_meta : CompFmu;
  }
  part def Unmarked {
    attribute fmu_meta : CompFmu;
  }
  part def Nested :> FmuModel {
    attribute fmu_meta : CompFmu;
    part inner : Comp;
  }
}
