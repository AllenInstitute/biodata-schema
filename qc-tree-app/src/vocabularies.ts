export const QC_STAGES = ["Raw data", "Processing", "Analysis", "Multi-asset"] as const;
export type Stage = (typeof QC_STAGES)[number];

export const MODALITIES = [
  { name: "Barcoded anatomy resolved by sequencing", abbreviation: "BARseq" },
  { name: "Behavior", abbreviation: "behavior" },
  { name: "Behavior videos", abbreviation: "behavior-videos" },
  { name: "Brightfield microscopy", abbreviation: "brightfield" },
  { name: "Confocal microscopy", abbreviation: "confocal" },
  { name: "Extracellular electrophysiology", abbreviation: "ecephys" },
  { name: "Electron microscopy", abbreviation: "EM" },
  { name: "Electromyography", abbreviation: "EMG" },
  { name: "Fiber photometry", abbreviation: "fib" },
  { name: "Fluorescence micro-optical sectioning tomography", abbreviation: "fMOST" },
  { name: "Intracellular electrophysiology", abbreviation: "icephys" },
  { name: "Intrinsic signal imaging", abbreviation: "ISI" },
  { name: "Multiplexed analysis of projections by sequencing", abbreviation: "MAPseq" },
  { name: "Multiplexed error-robust fluorescence in situ hybridization", abbreviation: "merfish" },
  { name: "Magnetic resonance imaging", abbreviation: "MRI" },
  { name: "One-photon imaging", abbreviation: "one-photon" },
  { name: "Planar optical physiology", abbreviation: "pophys" },
  { name: "Single cell RNA sequencing", abbreviation: "scRNAseq" },
  { name: "Random access projection microscopy", abbreviation: "slap2" },
  { name: "Selective plane illumination microscopy", abbreviation: "SPIM" },
  { name: "Serial two-photon tomogrophy", abbreviation: "STPT" },
] as const;

export type Modality = (typeof MODALITIES)[number]["abbreviation"];
