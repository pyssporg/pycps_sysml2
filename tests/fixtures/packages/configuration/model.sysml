package Fixed {
  private import Alpha::*;
  private import Beta::*;

  part def SspModel;

  part def Step;

  part def System :> SspModel {
    variation part source : SourceChoice;
  }

  part def StepSystem :> System {
    part :>> source = Alpha::SourceChoice::step;
  }

  part def Config {
    part sut : StepSystem;
  }
}
