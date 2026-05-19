#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ISQ (International System of Quantities) type/unit conformance validator.

Validates that pint units are semantically conformant to their expected ISQ types
by comparing dimensional analysis.
"""

import pint

ureg = pint.UnitRegistry()


# ISQ base quantity dimensions (ISO/IEC 80000)
# L = Length, M = Mass, T = Time, I = Electric Current,
# Theta = Thermodynamic Temperature, N = Amount of Substance, J = Luminous Intensity

# Mapping of ISQ Value types to their expected pint dimensions
# Format: 'ValueTypeName': pint.Dimensionality
ISQ_TYPE_DIMENSIONS = {
    # Base quantities (ISQBase)
    'LengthValue': {'[length]': 1},
    'DurationValue': {'[time]': 1},
    'MassValue': {'[mass]': 1},
    'ThermodynamicTemperatureValue': {'[temperature]': 1},
    'ElectricCurrentValue': {'[current]': 1},
    'LuminousIntensityValue': {'[luminous_intensity]': 1},
    'AmountOfSubstanceValue': {'[substance]': 1},

    # Space and Time (ISQSpaceTime)
    'WidthValue': {'[length]': 1},
    'HeightValue': {'[length]': 1},
    'DiameterValue': {'[length]': 1},
    'RadiusValue': {'[length]': 1},
    'DistanceValue': {'[length]': 1},
    'PositionVectorValue': {'[length]': 1},
    'DisplacementValue': {'[length]': 1},
    'AreaValue': {'[length]': 2},
    'VolumeValue': {'[length]': 3},
    'AngularMeasureValue': {},  # dimensionless
    'SolidAngularMeasureValue': {},  # dimensionless
    'SpeedValue': {'[length]': 1, '[time]': -1},
    'VelocityValue': {'[length]': 1, '[time]': -1},
    'AngularVelocityValue': {'[time]': -1},
    'AccelerationValue': {'[length]': 1, '[time]': -2},
    'AngularAccelerationValue': {'[time]': -2},
    'FrequencyValue': {'[time]': -1},
    'AngularFrequencyValue': {'[time]': -1},
    'WavelengthValue': {'[length]': 1},
    'WavenumberValue': {'[length]': -1},
    'CurvatureValue': {'[length]': -1},
    'DurationValue': {'[time]': 1},
    'TimeConstantValue': {'[time]': 1},
    'PeriodValue': {'[time]': 1},
    'HalfLifeValue': {'[time]': 1},

    # Mechanics (ISQMechanics)
    'MassDensityValue': {'[length]': -3, '[mass]': 1},
    'DensityValue': {'[length]': -3, '[mass]': 1},
    'SpecificVolumeValue': {'[length]': 3, '[mass]': -1},
    'RelativeMassDensityValue': {},  # dimensionless
    'RelativeDensityValue': {},  # dimensionless
    'SurfaceMassDensityValue': {'[length]': -2, '[mass]': 1},
    'SurfaceDensityValue': {'[length]': -2, '[mass]': 1},
    'LinearMassDensityValue': {'[length]': -1, '[mass]': 1},
    'LinearDensityValue': {'[length]': -1, '[mass]': 1},
    'MomentOfInertiaValue': {'[length]': 2, '[mass]': 1},
    'MomentumValue': {'[length]': 1, '[mass]': 1, '[time]': -1},
    'ForceValue': {'[length]': 1, '[mass]': 1, '[time]': -2},
    'ImpulseValue': {'[length]': 1, '[mass]': 1, '[time]': -1},
    'AngularMomentumValue': {'[length]': 2, '[mass]': 1, '[time]': -1},
    'MomentOfForceValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'TorqueValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'AngularImpulseValue': {'[length]': 2, '[mass]': 1, '[time]': -1},
    'PressureValue': {'[length]': -1, '[mass]': 1, '[time]': -2},
    'GaugePressureValue': {'[length]': -1, '[mass]': 1, '[time]': -2},
    'StressValue': {'[length]': -1, '[mass]': 1, '[time]': -2},
    'NormalStressValue': {'[length]': -1, '[mass]': 1, '[time]': -2},
    'ShearStressValue': {'[length]': -1, '[mass]': 1, '[time]': -2},
    'StrainValue': {},  # dimensionless
    'RelativeLinearStrainValue': {},  # dimensionless
    'ShearStrainValue': {},  # dimensionless
    'RelativeVolumeStrainValue': {},  # dimensionless
    'PoissonNumberValue': {},  # dimensionless
    'ModulusOfElasticityValue': {'[length]': -1, '[mass]': 1, '[time]': -2},
    'YoungModulusValue': {'[length]': -1, '[mass]': 1, '[time]': -2},
    'ModulusOfRigidityValue': {'[length]': -1, '[mass]': 1, '[time]': -2},
    'ShearModulusValue': {'[length]': -1, '[mass]': 1, '[time]': -2},
    'ModulusOfCompressionValue': {'[length]': -1, '[mass]': 1, '[time]': -2},
    'BulkModulusValue': {'[length]': -1, '[mass]': 1, '[time]': -2},
    'CompressibilityValue': {'[length]': 1, '[mass]': -1, '[time]': 2},
    'SecondAxialMomentOfAreaValue': {'[length]': 4},
    'SecondPolarMomentOfAreaValue': {'[length]': 4},
    'EnergyValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'WorkValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'KineticEnergyValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'PotentialEnergyValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'PowerValue': {'[length]': 2, '[mass]': 1, '[time]': -3},
    'MechanicalImpedanceValue': {'[length]': -1, '[mass]': 1, '[time]': -1},
    'MomentOfMomentumValue': {'[length]': 2, '[mass]': 1, '[time]': -1},
    'MassFlowRateValue': {'[mass]': 1, '[time]': -1},
    'MassFlowValue': {'[mass]': 1, '[time]': -1},
    'VolumeFlowRateValue': {'[length]': 3, '[time]': -1},
    'DynamicViscosityValue': {'[length]': -1, '[mass]': 1, '[time]': -1},
    'KinematicViscosityValue': {'[length]': 2, '[time]': -1},
    'SurfaceTensionValue': {'[mass]': 1, '[time]': -2},
    'FrictionFactorValue': {},  # dimensionless
    'ReynoldsNumberValue': {},  # dimensionless

    # Thermodynamics (ISQThermodynamics)
    'TemperatureValue': {'[temperature]': 1},
    'TemperatureDifferenceValue': {'[temperature]': 1},
    'LinearExpansionCoefficientValue': {'[temperature]': -1},
    'CubicExpansionCoefficientValue': {'[temperature]': -1},
    'PressureCoefficientValue': {'[length]': -1, '[mass]': 1, '[time]': -2, '[temperature]': -1},
    'RelativePressureCoefficientValue': {'[temperature]': -1},
    'HeatCapacityValue': {'[length]': 2, '[mass]': 1, '[time]': -2, '[temperature]': -1},
    'SpecificHeatCapacityValue': {'[length]': 2, '[time]': -2, '[temperature]': -1},
    'MolarHeatCapacityValue': {'[length]': 2, '[mass]': 1, '[time]': -2, '[temperature]': -1, '[substance]': -1},
    'EntropyValue': {'[length]': 2, '[mass]': 1, '[time]': -2, '[temperature]': -1},
    'SpecificEntropyValue': {'[length]': 2, '[time]': -2, '[temperature]': -1},
    'MolarEntropyValue': {'[length]': 2, '[mass]': 1, '[time]': -2, '[temperature]': -1, '[substance]': -1},
    'EnthalpyValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'SpecificEnthalpyValue': {'[length]': 2, '[time]': -2},
    'MolarEnthalpyValue': {'[length]': 2, '[mass]': 1, '[time]': -2, '[substance]': -1},
    'GibbsEnergyValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'SpecificGibbsEnergyValue': {'[length]': 2, '[time]': -2},
    'MolarGibbsEnergyValue': {'[length]': 2, '[mass]': 1, '[time]': -2, '[substance]': -1},
    'HelmholtzEnergyValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'SpecificHelmholtzEnergyValue': {'[length]': 2, '[time]': -2},
    'MolarHelmholtzEnergyValue': {'[length]': 2, '[mass]': 1, '[time]': -2, '[substance]': -1},
    'HeatValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'HeatFlowRateValue': {'[length]': 2, '[mass]': 1, '[time]': -3},
    'ThermalConductivityValue': {'[length]': 1, '[mass]': 1, '[time]': -3, '[temperature]': -1},
    'ThermalConductanceValue': {'[length]': 2, '[mass]': 1, '[time]': -3, '[temperature]': -1},
    'ThermalResistanceValue': {'[length]': -2, '[mass]': -1, '[time]': 3, '[temperature]': 1},
    'ThermalInsulanceValue': {'[length]': -2, '[mass]': -1, '[time]': 3, '[temperature]': 1},
    'ThermalDiffusivityValue': {'[length]': 2, '[time]': -1},
    'HeatOfFusionValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'SpecificHeatOfFusionValue': {'[length]': 2, '[time]': -2},
    'MolarHeatOfFusionValue': {'[length]': 2, '[mass]': 1, '[time]': -2, '[substance]': -1},
    'HeatOfVaporizationValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'SpecificHeatOfVaporizationValue': {'[length]': 2, '[time]': -2},
    'MolarHeatOfVaporizationValue': {'[length]': 2, '[mass]': 1, '[time]': -2, '[substance]': -1},
    'HeatOfSublimationValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'SpecificHeatOfSublimationValue': {'[length]': 2, '[time]': -2},
    'MolarHeatOfSublimationValue': {'[length]': 2, '[mass]': 1, '[time]': -2, '[substance]': -1},
    'JouleThomsonCoefficientValue': {'[length]': 1, '[mass]': -1, '[time]': 2, '[temperature]': 1},
    'FugacityValue': {'[length]': -1, '[mass]': 1, '[time]': -2},
    'ActivityValue': {},  # dimensionless
    'OsmoticPressureValue': {'[length]': -1, '[mass]': 1, '[time]': -2},
    'ChemicalPotentialValue': {'[length]': 2, '[mass]': 1, '[time]': -2, '[substance]': -1},
    'MassFractionValue': {},  # dimensionless
    'MoleFractionValue': {},  # dimensionless
    'VolumeFractionValue': {},  # dimensionless
    'AmountOfSubstanceConcentrationValue': {'[length]': -3, '[substance]': 1},
    'MolalityValue': {'[mass]': -1, '[substance]': 1},
    'SolubilityValue': {'[length]': -3, '[substance]': 1},
    'PHValue': {},  # dimensionless
    'BufferCapacityValue': {'[length]': -3, '[substance]': 1},
    'DegreeOfDissociationValue': {},  # dimensionless
    'DegreeOfAssociationValue': {},  # dimensionless
    'IonicStrengthValue': {'[mass]': -1, '[substance]': 1},
    'EquilibriumConstantOnPressureBasisValue': {},  # dimensionless
    'EquilibriumConstantOnConcentrationBasisValue': {'[length]': -3, '[substance]': 1},
    'HenryLawConstantValue': {'[length]': -1, '[mass]': 1, '[time]': -2},
    'DissociationConstantValue': {'[length]': -3, '[substance]': 1},

    # Electromagnetism (ISQElectromagnetism)
    'ElectricChargeValue': {'[current]': 1, '[time]': 1},
    'ElectricChargeDensityValue': {'[length]': -3, '[current]': 1, '[time]': 1},
    'SurfaceDensityOfElectricChargeValue': {'[length]': -2, '[current]': 1, '[time]': 1},
    'LinearDensityOfElectricChargeValue': {'[length]': -1, '[current]': 1, '[time]': 1},
    'ElectricCurrentValue': {'[current]': 1},
    'ElectricCurrentDensityValue': {'[length]': -2, '[current]': 1},
    'LinearElectricCurrentDensityValue': {'[length]': -1, '[current]': 1},
    'ElectricFieldStrengthValue': {'[length]': 1, '[mass]': 1, '[time]': -3, '[current]': -1},
    'ElectricPotentialValue': {'[length]': 2, '[mass]': 1, '[time]': -3, '[current]': -1},
    'ElectricPotentialDifferenceValue': {'[length]': 2, '[mass]': 1, '[time]': -3, '[current]': -1},
    'VoltageValue': {'[length]': 2, '[mass]': 1, '[time]': -3, '[current]': -1},
    'ElectricDipoleMomentValue': {'[current]': 1, '[time]': 1, '[length]': 1},
    'ElectricFluxValue': {'[length]': 3, '[mass]': 1, '[time]': -3, '[current]': -1},
    'ElectricDisplacementFieldStrengthValue': {'[length]': -2, '[current]': 1, '[time]': 1},
    'PermittivityValue': {'[length]': -3, '[mass]': -1, '[time]': 4, '[current]': 2},
    'ElectricConstantValue': {'[length]': -3, '[mass]': -1, '[time]': 4, '[current]': 2},
    'RelativePermittivityValue': {},  # dimensionless
    'CapacitanceValue': {'[length]': -2, '[mass]': -1, '[time]': 4, '[current]': 2},
    'ResistanceValue': {'[length]': 2, '[mass]': 1, '[time]': -3, '[current]': -2},
    'ResistivityValue': {'[length]': 3, '[mass]': 1, '[time]': -3, '[current]': -2},
    'ConductanceValue': {'[length]': -2, '[mass]': -1, '[time]': 3, '[current]': 2},
    'ConductivityValue': {'[length]': -3, '[mass]': -1, '[time]': 3, '[current]': 2},
    'ElectrolyticConductivityValue': {'[length]': -3, '[mass]': -1, '[time]': 3, '[current]': 2},
    'MolarConductivityValue': {'[mass]': -1, '[time]': 3, '[current]': 2, '[substance]': -1},
    'MagneticFluxValue': {'[length]': 2, '[mass]': 1, '[time]': -2, '[current]': -1},
    'MagneticFluxDensityValue': {'[mass]': 1, '[time]': -2, '[current]': -1},
    'MagneticFieldStrengthValue': {'[length]': -1, '[current]': 1},
    'MagneticDipoleMomentValue': {'[length]': 2, '[current]': 1},
    'MagneticVectorPotentialValue': {'[length]': 1, '[mass]': 1, '[time]': -2, '[current]': -1},
    'PermeabilityValue': {'[length]': 1, '[mass]': 1, '[time]': -2, '[current]': -2},
    'MagneticConstantValue': {'[length]': 1, '[mass]': 1, '[time]': -2, '[current]': -2},
    'RelativePermeabilityValue': {},  # dimensionless
    'InductanceValue': {'[length]': 2, '[mass]': 1, '[time]': -2, '[current]': -2},
    'PermeanceValue': {'[length]': -2, '[mass]': -1, '[time]': 2, '[current]': 2},
    'ReluctanceValue': {'[length]': -2, '[mass]': -1, '[time]': 2, '[current]': -2},
    'MobilityValue': {'[length]': -1, '[mass]': -1, '[time]': 3, '[current]': 1},
    'HallCoefficientValue': {'[length]': 3, '[mass]': 1, '[time]': -3, '[current]': -2},
    'SeebeckCoefficientForSubstancesAAndBValue': {'[length]': 2, '[mass]': 1, '[time]': -3, '[current]': -1, '[temperature]': -1},
    'ExposureValue': {'[mass]': -1, '[current]': 1, '[time]': 1},
    'ExposureRateValue': {'[mass]': -1, '[current]': 1},
    'AbsorbedDoseValue': {'[length]': 2, '[time]': -2},
    'DoseEquivalentValue': {'[length]': 2, '[time]': -2},
    'KermaValue': {'[length]': 2, '[time]': -2},
    'ActivityValue': {'[time]': -1},
    'NuclearActivityValue': {'[time]': -1},

    # Light (ISQLight)
    'LuminousEnergyValue': {'[luminous_intensity]': 1, '[time]': 1},
    'LuminousFluxValue': {'[luminous_intensity]': 1},
    'LuminousIntensityValue': {'[luminous_intensity]': 1},
    'LuminanceValue': {'[luminous_intensity]': 1},
    'IlluminanceValue': {'[luminous_intensity]': 1},
    'LuminousExitanceValue': {'[luminous_intensity]': 1},
    'LuminousExposureValue': {'[luminous_intensity]': 1, '[time]': 1},
    'LuminousEfficacyOfRadiationValue': {'[length]': -2, '[mass]': -1, '[time]': 3, '[luminous_intensity]': 1},
    'RadiantEnergyValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'RadiantFluxValue': {'[length]': 2, '[mass]': 1, '[time]': -3},
    'RadiantIntensityValue': {'[length]': 2, '[mass]': 1, '[time]': -3},
    'RadianceValue': {'[mass]': 1, '[time]': -3},
    'IrradianceValue': {'[mass]': 1, '[time]': -3},
    'RadiantExitanceValue': {'[mass]': 1, '[time]': -3},
    'RadiantExposureValue': {'[mass]': 1, '[time]': -2},
    'SpectralRadiantEnergyValue': {'[length]': 1, '[mass]': 1, '[time]': -2},
    'SpectralRadiantFluxValue': {'[length]': 1, '[mass]': 1, '[time]': -3},
    'SpectralRadiantIntensityValue': {'[length]': 1, '[mass]': 1, '[time]': -3},
    'SpectralRadianceValue': {'[length]': -1, '[mass]': 1, '[time]': -3},
    'SpectralIrradianceValue': {'[length]': -1, '[mass]': 1, '[time]': -3},
    'SpectralRadiantExitanceValue': {'[length]': -1, '[mass]': 1, '[time]': -3},
    'SpectralRadiantExposureValue': {'[length]': -1, '[mass]': 1, '[time]': -2},
    'RadiantEnergyDensityValue': {'[length]': -1, '[mass]': 1, '[time]': -2},
    'SpectralRadiantEnergyDensityInTermsOfWavelengthValue': {'[length]': -2, '[mass]': 1, '[time]': -2},
    'SpectralRadiantEnergyDensityInTermsOfWavenumberValue': {'[length]': -2, '[mass]': 1, '[time]': -2},
    'SpectralRadiantEnergyDensityInTermsOfFrequencyValue': {'[length]': 1, '[mass]': 1, '[time]': -1},
    'LuminousEfficacyValue': {'[length]': -2, '[mass]': -1, '[time]': 3, '[luminous_intensity]': 1},

    # Acoustics (ISQAcoustics)
    'SoundPressureValue': {'[length]': -1, '[mass]': 1, '[time]': -2},
    'SoundPowerValue': {'[length]': 2, '[mass]': 1, '[time]': -3},
    'SoundEnergyValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'SoundIntensityValue': {'[mass]': 1, '[time]': -3},
    'SoundExposureValue': {'[length]': -2, '[mass]': 2, '[time]': -3},
    'AcousticImpedanceValue': {'[length]': -4, '[mass]': 1, '[time]': -1},
    'CharacteristicImpedanceOfAMediumForLongitudinalWavesValue': {'[length]': -1, '[mass]': 1, '[time]': -1},
    'SoundPressureLevelValue': {},  # dimensionless (logarithmic)
    'SoundPowerLevelValue': {},  # dimensionless (logarithmic)
    'SoundIntensityLevelValue': {},  # dimensionless (logarithmic)
    'SoundExposureLevelValue': {},  # dimensionless (logarithmic)

    # Chemistry/Molecular (ISQChemistryMolecular)
    'CatalyticActivityValue': {'[time]': -1, '[substance]': 1},
    'CatalyticActivityConcentrationValue': {'[length]': -3, '[time]': -1, '[substance]': 1},

    # Atomic/Nuclear (ISQAtomicNuclear)
    'AbsorbedDoseValue': {'[length]': 2, '[time]': -2},
    'DoseEquivalentValue': {'[length]': 2, '[time]': -2},
    'KermaValue': {'[length]': 2, '[time]': -2},
    'SpecificEnergyValue': {'[length]': 2, '[time]': -2},
    'LinearEnergyTransferValue': {'[length]': 1, '[mass]': 1, '[time]': -2},
    'ActivityValue': {'[time]': -1},
    'NuclearActivityValue': {'[time]': -1},
    'SurfaceActivityDensityValue': {'[length]': -2, '[time]': -1},
    'ActivityDensityValue': {'[length]': -3, '[time]': -1},
    'SpecificActivityValue': {'[mass]': -1, '[time]': -1},
    'FluenceValue': {'[length]': -2},
    'FluenceRateValue': {'[length]': -2, '[time]': -1},
    'EnergyFluenceValue': {'[length]': -1, '[mass]': 1, '[time]': -2},
    'EnergyFluenceRateValue': {'[length]': -1, '[mass]': 1, '[time]': -3},
    'CrossSectionValue': {'[length]': 2},
    'TotalCrossSectionValue': {'[length]': 2},
    'DifferentialCrossSectionValue': {},  # dimensionless (per steradian)
    'DirectionDistributionOfCrossSectionValue': {'[length]': 2},
    'EnergyDistributionOfCrossSectionValue': {'[length]': 2, '[mass]': -1, '[time]': 2},
    'DirectionAndEnergyDistributionOfCrossSectionValue': {'[length]': 2, '[mass]': -1, '[time]': 2},
    'MassAttenuationCoefficientValue': {'[mass]': -1, '[length]': 2},
    'MassEnergyTransferCoefficientValue': {'[mass]': -1, '[length]': 2},
    'MassEnergyAbsorptionCoefficientValue': {'[mass]': -1, '[length]': 2},
    'TotalLinearAttenuationCoefficientValue': {'[length]': -1},
    'TotalLinearEnergyTransferCoefficientValue': {'[length]': -1},
    'TotalLinearEnergyAbsorptionCoefficientValue': {'[length]': -1},
    'TotalMassStoppingPowerValue': {'[length]': 4, '[mass]': -1, '[time]': -2},
    'TotalLinearStoppingPowerValue': {'[length]': 1, '[mass]': 1, '[time]': -2},
    'RestrictedTotalMassStoppingPowerValue': {'[length]': 4, '[mass]': -1, '[time]': -2},
    'RestrictedTotalLinearStoppingPowerValue': {'[length]': 1, '[mass]': 1, '[time]': -2},
    'LinearCollisionStoppingPowerValue': {'[length]': 1, '[mass]': 1, '[time]': -2},
    'LinearRadiativeStoppingPowerValue': {'[length]': 1, '[mass]': 1, '[time]': -2},
    'MassCollisionStoppingPowerValue': {'[length]': 4, '[mass]': -1, '[time]': -2},
    'MassRadiativeStoppingPowerValue': {'[length]': 4, '[mass]': -1, '[time]': -2},
    'RadiationYieldValue': {},  # dimensionless
    'AbsorbedDoseRateValue': {'[length]': 2, '[time]': -3},
    'DoseEquivalentRateValue': {'[length]': 2, '[time]': -3},
    'KermaRateValue': {'[length]': 2, '[time]': -3},
    'SpecificEnergyRateValue': {'[length]': 2, '[time]': -3},
    'AbsorbedDoseRateConstantValue': {'[length]': 4, '[mass]': -1, '[time]': -1},
    'DoseEquivalentRateConstantValue': {'[length]': 4, '[mass]': -1, '[time]': -1},
    'KermaRateConstantValue': {'[length]': 4, '[mass]': -1, '[time]': -1},
    'SpecificEnergyRateConstantValue': {'[length]': 4, '[mass]': -1, '[time]': -1},
    'AmbientDoseEquivalentValue': {'[length]': 2, '[time]': -2},
    'DirectionalDoseEquivalentValue': {'[length]': 2, '[time]': -2},
    'PersonalDoseEquivalentValue': {'[length]': 2, '[time]': -2},
    'OrganDoseEquivalentValue': {'[length]': 2, '[time]': -2},
    'EffectiveDoseValue': {'[length]': 2, '[time]': -2},
    'CommittedEffectiveDoseValue': {'[length]': 2, '[time]': -2},
    'EquivalentDoseValue': {'[length]': 2, '[time]': -2},
    'CommittedEquivalentDoseValue': {'[length]': 2, '[time]': -2},
    'AbsorbedFractionValue': {},  # dimensionless
    'SpecificAbsorbedFractionValue': {'[mass]': -1},
    'SEEValue': {'[length]': 2, '[time]': -2, '[mass]': -1},
    'EffectiveEnergyValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'EffectiveEnergySquaredValue': {'[length]': 4, '[mass]': 2, '[time]': -4},
    'MeanEnergyValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'MeanEnergyImpartedValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'LinealEnergyValue': {'[length]': 1, '[mass]': 1, '[time]': -2},
    'SpecificEnergyZValue': {'[length]': 2, '[time]': -2},
    'EnergyImpartedValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'NetEnergyImpartedValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'GyromagneticRatioValue': {'[mass]': -1, '[time]': 1, '[current]': 1},
    'GyromagneticRatioOfProtonInWaterValue': {'[mass]': -1, '[time]': 1, '[current]': 1},
    'MagneticMomentValue': {'[length]': 2, '[current]': 1},
    'MagneticMomentOfProtonInWaterValue': {'[length]': 2, '[current]': 1},
    'NuclearMagneticDipoleMomentValue': {'[length]': 2, '[current]': 1},
    'NuclearElectricQuadrupoleMomentValue': {'[length]': 2, '[current]': 1, '[time]': 1},
    'MagneticShieldingFactorValue': {},  # dimensionless
    'ChemicalShiftValue': {},  # dimensionless
    'CouplingConstantValue': {'[time]': -1},
    'SpinLatticeRelaxationTimeValue': {'[time]': 1},
    'SpinSpinRelaxationTimeValue': {'[time]': 1},
    'LongitudinalRelaxationTimeValue': {'[time]': 1},
    'TransverseRelaxationTimeValue': {'[time]': 1},
    'NuclearOverhauserEnhancementValue': {},  # dimensionless
    'HartreeEnergyValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'RydbergConstantValue': {'[length]': -1},
    'BohrRadiusValue': {'[length]': 1},
    'FineStructureConstantValue': {},  # dimensionless
    'ClassicalElectronRadiusValue': {'[length]': 1},
    'ThomsonCrossSectionValue': {'[length]': 2},
    'ComptonWavelengthValue': {'[length]': 1},
    'ReducedComptonWavelengthValue': {'[length]': 1},
    'FermiCouplingConstantValue': {'[length]': 4, '[mass]': 1, '[time]': -2},
    'WeakMixingAngleValue': {},  # dimensionless
    'SineSquaredWeakMixingAngleValue': {},  # dimensionless
    'WbosonMassValue': {'[mass]': 1},
    'ZbosonMassValue': {'[mass]': 1},
    'HiggsBosonMassValue': {'[mass]': 1},
    'TopQuarkMassValue': {'[mass]': 1},
    'CharmQuarkMassValue': {'[mass]': 1},
    'BottomQuarkMassValue': {'[mass]': 1},
    'StrangeQuarkMassValue': {'[mass]': 1},
    'UpQuarkMassValue': {'[mass]': 1},
    'DownQuarkMassValue': {'[mass]': 1},
    'ElectronMassValue': {'[mass]': 1},
    'MuonMassValue': {'[mass]': 1},
    'TauMassValue': {'[mass]': 1},
    'ProtonMassValue': {'[mass]': 1},
    'NeutronMassValue': {'[mass]': 1},
    'DeuteronMassValue': {'[mass]': 1},
    'TritonMassValue': {'[mass]': 1},
    'HelionMassValue': {'[mass]': 1},
    'AlphaParticleMassValue': {'[mass]': 1},

    # Characteristic Numbers (ISQCharacteristicNumbers)
    'ReynoldsNumberValue': {},  # dimensionless
    'MachNumberValue': {},  # dimensionless
    'PrandtlNumberValue': {},  # dimensionless
    'NusseltNumberValue': {},  # dimensionless
    'GrashofNumberValue': {},  # dimensionless
    'PecletNumberValue': {},  # dimensionless
    'StrouhalNumberValue': {},  # dimensionless
    'FroudeNumberValue': {},  # dimensionless
    'EulerNumberValue': {},  # dimensionless
    'WeberNumberValue': {},  # dimensionless
    'CauchyNumberValue': {},  # dimensionless
    'NewtonNumberValue': {},  # dimensionless
    'KnudsenNumberValue': {},  # dimensionless
    'StantonNumberValue': {},  # dimensionless
    'SchmidtNumberValue': {},  # dimensionless
    'LewisNumberValue': {},  # dimensionless
    'SherwoodNumberValue': {},  # dimensionless
    'FourierNumberValue': {},  # dimensionless
    'BiotNumberValue': {},  # dimensionless
    'DamkohlerNumberValue': {},  # dimensionless
    'ThieleModulusValue': {},  # dimensionless
    'WomersleyNumberValue': {},  # dimensionless
    'ArchimedesNumberValue': {},  # dimensionless
    'RayleighNumberValue': {},  # dimensionless
    'TaylorNumberValue': {},  # dimensionless
    'DeborahNumberValue': {},  # dimensionless
    'WeissenbergNumberValue': {},  # dimensionless
    'CapillaryNumberValue': {},  # dimensionless
    'OhnesorgeNumberValue': {},  # dimensionless
    'BondNumberValue': {},  # dimensionless
    'EotvosNumberValue': {},  # dimensionless
    'MortonNumberValue': {},  # dimensionless
    'RouseNumberValue': {},  # dimensionless
    'HagenNumberValue': {},  # dimensionless
    'GalileoNumberValue': {},  # dimensionless
    'KarlovitzNumberValue': {},  # dimensionless
    'BodensteinNumberValue': {},  # dimensionless
    'BejanNumberValue': {},  # dimensionless
    'ColburnFactorValue': {},  # dimensionless
    'StantonFactorValue': {},  # dimensionless
    'FrictionFactorValue': {},  # dimensionless
    'DragCoefficientValue': {},  # dimensionless
    'LiftCoefficientValue': {},  # dimensionless
    'PressureCoefficientValue': {'[length]': -1, '[mass]': 1, '[time]': -2, '[temperature]': -1},
    'RecoveryFactorValue': {},  # dimensionless
    'ShapeFactorValue': {},  # dimensionless
    'BlockageFactorValue': {},  # dimensionless
    'ContractionCoefficientValue': {},  # dimensionless
    'DischargeCoefficientValue': {},  # dimensionless
    'FlowCoefficientValue': {},  # dimensionless
    'ResistanceCoefficientValue': {},  # dimensionless
    'LossCoefficientValue': {},  # dimensionless
    'VelocityCoefficientValue': {},  # dimensionless
    'EfficiencyValue': {},  # dimensionless
    'EffectivenessValue': {},  # dimensionless
    'PerformanceCoefficientValue': {},  # dimensionless
    'QualityFactorValue': {},  # dimensionless
    'FigureOfMeritValue': {},  # dimensionless
    'CoefficientOfPerformanceValue': {},  # dimensionless
    'EnergyEfficiencyRatioValue': {},  # dimensionless
    'SeasonalEnergyEfficiencyRatioValue': {},  # dimensionless
    'HeatingSeasonalPerformanceFactorValue': {},  # dimensionless
    'AnnualFuelUtilizationEfficiencyValue': {},  # dimensionless
    'ThermalEfficiencyValue': {},  # dimensionless
    'MechanicalEfficiencyValue': {},  # dimensionless
    'VolumetricEfficiencyValue': {},  # dimensionless
    'IsentropicEfficiencyValue': {},  # dimensionless
    'PolytropicEfficiencyValue': {},  # dimensionless
    'AdiabaticEfficiencyValue': {},  # dimensionless
    'CombustionEfficiencyValue': {},  # dimensionless
    'PropulsiveEfficiencyValue': {},  # dimensionless
    'OverallEfficiencyValue': {},  # dimensionless
    'TransmissionEfficiencyValue': {},  # dimensionless
    'ConversionEfficiencyValue': {},  # dimensionless
    'GeneratorEfficiencyValue': {},  # dimensionless
    'MotorEfficiencyValue': {},  # dimensionless
    'PumpEfficiencyValue': {},  # dimensionless
    'TurbineEfficiencyValue': {},  # dimensionless
    'CompressorEfficiencyValue': {},  # dimensionless
    'FanEfficiencyValue': {},  # dimensionless
    'BlowerEfficiencyValue': {},  # dimensionless

    # Condensed Matter (ISQCondensedMatter)
    'FermiEnergyValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'FermiTemperatureValue': {'[temperature]': 1},
    'FermiWavevectorValue': {'[length]': -1},
    'FermiVelocityValue': {'[length]': 1, '[time]': -1},
    'FermiMomentumValue': {'[length]': 1, '[mass]': 1, '[time]': -1},
    'DensityOfStatesValue': {'[length]': -5, '[mass]': -1, '[time]': 2},
    'EnergyDensityOfStatesValue': {'[length]': -5, '[mass]': -1, '[time]': 2},
    'EffectiveMassValue': {'[mass]': 1},
    'EffectiveMassTensorValue': {'[mass]': 1},
    'EffectiveGFactorValue': {},  # dimensionless
    'LandauLevelValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'CyclotronFrequencyValue': {'[time]': -1},
    'CyclotronMassValue': {'[mass]': 1},
    'CyclotronResonanceValue': {'[time]': -1},
    'PlasmaFrequencyValue': {'[time]': -1},
    'DebyeTemperatureValue': {'[temperature]': 1},
    'DebyeFrequencyValue': {'[time]': -1},
    'DebyeWavelengthValue': {'[length]': 1},
    'DebyeWavevectorValue': {'[length]': -1},
    'DebyeLengthValue': {'[length]': 1},
    'DebyeScreeningLengthValue': {'[length]': 1},
    'ThomasFermiScreeningLengthValue': {'[length]': 1},
    'ScreeningLengthValue': {'[length]': 1},
    'ScreeningWavevectorValue': {'[length]': -1},
    'ScreeningEnergyValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'ScreeningPotentialValue': {'[length]': 2, '[mass]': 1, '[time]': -3, '[current]': -1},
    'ScreeningChargeValue': {'[current]': 1, '[time]': 1},
    'ScreeningChargeDensityValue': {'[length]': -3, '[current]': 1, '[time]': 1},
    'ScreeningCurrentDensityValue': {'[length]': -2, '[current]': 1},
    'ScreeningCurrentValue': {'[current]': 1},
    'ScreeningMagneticFieldValue': {'[mass]': 1, '[time]': -2, '[current]': -1},
    'ScreeningElectricFieldValue': {'[length]': 1, '[mass]': 1, '[time]': -3, '[current]': -1},
    'ScreeningDisplacementFieldValue': {'[length]': -2, '[current]': 1, '[time]': 1},
    'ScreeningPolarizationValue': {'[length]': -2, '[current]': 1, '[time]': 1},
    'ScreeningMagnetizationValue': {'[length]': -1, '[current]': 1},
    'ScreeningSusceptibilityValue': {},  # dimensionless
    'ScreeningPermittivityValue': {'[length]': -3, '[mass]': -1, '[time]': 4, '[current]': 2},
    'ScreeningPermeabilityValue': {'[length]': 1, '[mass]': 1, '[time]': -2, '[current]': -2},
    'ScreeningConductivityValue': {'[length]': -3, '[mass]': -1, '[time]': 3, '[current]': 2},
    'ScreeningResistivityValue': {'[length]': 3, '[mass]': 1, '[time]': -3, '[current]': -2},
    'ScreeningMobilityValue': {'[length]': -1, '[mass]': -1, '[time]': 3, '[current]': 1},
    'ScreeningDiffusionCoefficientValue': {'[length]': 2, '[time]': -1},
    'ScreeningDiffusivityValue': {'[length]': 2, '[time]': -1},
    'ScreeningThermalConductivityValue': {'[length]': 1, '[mass]': 1, '[time]': -3, '[temperature]': -1},
    'ScreeningThermalDiffusivityValue': {'[length]': 2, '[time]': -1},
    'ScreeningViscosityValue': {'[length]': -1, '[mass]': 1, '[time]': -1},
    'ScreeningKinematicViscosityValue': {'[length]': 2, '[time]': -1},
    'ScreeningSurfaceTensionValue': {'[mass]': 1, '[time]': -2},
    'ScreeningInterfacialTensionValue': {'[mass]': 1, '[time]': -2},
    'ScreeningContactAngleValue': {},  # dimensionless
    'ScreeningWettingAngleValue': {},  # dimensionless
    'ScreeningSpreadingCoefficientValue': {'[mass]': 1, '[time]': -2},
    'ScreeningAdhesionWorkValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'ScreeningCohesionWorkValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'ScreeningSurfaceEnergyValue': {'[mass]': 1, '[time]': -2},
    'ScreeningSurfaceEntropyValue': {'[length]': 2, '[mass]': 1, '[time]': -2, '[temperature]': -1},
    'ScreeningSurfaceEnthalpyValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'ScreeningSurfaceFreeEnergyValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'ScreeningSurfaceGibbsEnergyValue': {'[length]': 2, '[mass]': 1, '[time]': -2},
    'ScreeningSurfaceHelmholtzEnergyValue': {'[length]': 2, '[mass]': 1, '[time]': -2},

    # Information (ISQInformation)
    'InformationContentValue': {},  # dimensionless (logarithmic)
    'StorageCapacityValue': {},  # dimensionless
    'TransferRateValue': {'[time]': -1},
    'BinaryDigitRateValue': {'[time]': -1},
    'AverageInformationRateValue': {'[time]': -1},
    'ModulationRateValue': {'[time]': -1},
    'TrafficIntensityValue': {},  # dimensionless
    'LogarithmicFrequencyRangeValue': {},  # dimensionless
}


def get_dimensionality(dim_dict):
    """Convert a dimension dictionary to pint Dimensionality."""
    return pint.util.to_units_container(dim_dict)


def validate_unit_conformance(value_type, unit):
    """
    Validate that a pint unit is conformant to an ISQ value type.

    Args:
        value_type: The ISQ value type name (e.g., 'LengthValue', 'MassValue')
        unit: A pint unit or quantity

    Returns:
        tuple: (is_conformant: bool, message: str)

    Raises:
        ValueError: If the value type is not recognized
    """
    if isinstance(unit, pint.Quantity):
        unit = unit.units

    if value_type not in ISQ_TYPE_DIMENSIONS:
        return True, f"Unknown ISQ type '{value_type}', skipping validation"

    expected_dims = get_dimensionality(ISQ_TYPE_DIMENSIONS[value_type])
    actual_dims = unit.dimensionality

    if expected_dims == actual_dims:
        return True, f"Unit '{unit}' is conformant to {value_type}"
    else:
        return False, (
            f"Unit '{unit}' is NOT conformant to {value_type}. "
            f"Expected dimension: {expected_dims}, "
            f"Got: {actual_dims}"
        )


def validate_quantity_conformance(value_type, quantity):
    """
    Validate that a pint quantity's unit is conformant to an ISQ value type.

    Args:
        value_type: The ISQ value type name (e.g., 'LengthValue', 'MassValue')
        quantity: A pint quantity

    Returns:
        tuple: (is_conformant: bool, message: str)
    """
    return validate_unit_conformance(value_type, quantity)


def get_expected_dimension(value_type):
    """
    Get the expected pint dimensionality for an ISQ value type.

    Args:
        value_type: The ISQ value type name

    Returns:
        pint.Dimensionality or None if type not found
    """
    if value_type not in ISQ_TYPE_DIMENSIONS:
        return None
    return get_dimensionality(ISQ_TYPE_DIMENSIONS[value_type])


def is_dimensionless_type(value_type):
    """
    Check if an ISQ value type is dimensionless.

    Args:
        value_type: The ISQ value type name

    Returns:
        bool: True if the type is dimensionless
    """
    if value_type not in ISQ_TYPE_DIMENSIONS:
        return False
    return len(ISQ_TYPE_DIMENSIONS[value_type]) == 0
