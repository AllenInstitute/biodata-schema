# External registries

External registries act as an application programming interfaces (API). They allow us to store metadata from registries that are too large to store inside of the `biodata-models` repository. Because of this, we can't enumerate all of the options for each model in the documentation. Instead we link here to the search page for each registry along with one example of what the atlas responses look like.

## Model definitions

### AnatomyModel

Shared Pydantic model for species-specific anatomy terms. Fields typed as `AnatomyModel` can use a lookup subclass such as `MouseAnatomyLookup` or `HumanAnatomyLookup`, which provides ontology-specific lookup behavior.

| Name | Registry | Registry Identifier |
|------|-------|--------|
| `heart` | `Registry.EMAPA` | `EMAPA:16105` |

### MouseAnatomyLookup

[EMAPA](https://www.ebi.ac.uk/ols4/ontologies/emapa)

Lookup model for mouse anatomy terms. Use `search_by_name` to find terms and `get_by_name` for an exact label match.

| Name | Registry | Registry Identifier |
|------|-------|--------|
| `heart` | `Registry.EMAPA` | `EMAPA:16105` |

### Gene

[GenBank](https://www.ncbi.nlm.nih.gov/genbank/)

Base model for genes. One example:

| Name | Description | Registry | Registry Identifier |
|------|------|-------|--------|
| `gfp` | `Human adenovirus B isolate 340-2010 DNA, complete genome` | `Registry.GENBANK` | `LN515608` |
