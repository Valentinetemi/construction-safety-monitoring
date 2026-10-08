# PPE model card and provenance

## Selected weights

- Repository: [`constructelligence/construction-site-safety-hazards`](https://huggingface.co/constructelligence/construction-site-safety-hazards)
- File: `buildvision-hazards-v0.3.pt`
- Pinned revision: `45d07d8e27a4754df1ea651f62153e000133bece`
- Architecture: Ultralytics YOLOv8s
- Input described by publisher: 640 × 640 letterboxed RGB
- PyTorch weight size shown by the repository: approximately 22.6 MB
- Weight licence declared by publisher: AGPL-3.0
- Training-data licences declared by publisher: CC BY 4.0

The weights are downloaded into the Hugging Face user cache at runtime. They are not stored in or committed to this repository.

## Published class definitions

The publisher lists these output classes:

1. `person`
2. `hardhat`
3. `no-hardhat`
4. `safety vest`
5. `no-safety vest`
6. `no-mask`
7. `gloves`
8. `safety shoes`
9. `excavator`
10. `wheel loader`
11. `dump truck`
12. `goggles`
13. `no-goggles`
14. `no-gloves`

SiteGuard intentionally consumes only hard-hat and safety-vest positive/negative classes. It does not turn an unsupported or absent class into a violation.

## Published training provenance

The model card states that 7,450 training and 567 validation images were assembled from these sources:

- Construction Site Safety (Roboflow Universe Projects)
- `construction-safety-gsnvb` (Roboflow 100)
- PPE detection 1 (vincentspace)
- PPE_Dectection v4 (himanshu-bharati)
- `excavators-czvg9` (Roboflow 100)

The publisher describes those datasets as CC BY 4.0 and states that person pseudo-labels in its test set came from Ultralytics YOLOv8s (COCO).

## Why this model was chosen

It has downloadable local weights, a documented licence, documented training sources, explicit helmet/vest positive and negative labels, a modest model size, and direct Ultralytics compatibility. That satisfies the project more responsibly than applying a generic COCO detector to PPE.

## Limitations carried into SiteGuard

The publisher reports weaker held-out results for missing PPE than for worn PPE and explicitly says the model is decision support rather than a compliance record. SiteGuard preserves that boundary by requiring temporal evidence, using the term `POSSIBLE_VIOLATION`, saving the evidence frame, and requiring human review.

The model card's metrics are the publisher's self-reported results on its test set. They are not SiteGuard evaluation results and are not copied into SiteGuard summaries.
