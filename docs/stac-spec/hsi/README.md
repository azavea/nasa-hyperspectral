# Hyperspectral Imagery Extension Specification

- **Title:** Hyperspectral Imagery
- **Identifier:** https://github.com/azavea/nasa-hyperspectral/tree/master/docs/stac/hsi/json-schema/schema.json
- **Field Name Prefix:** hsi
- **Scope:** Item, Collection
- **Extension [Maturity Classification](https://github.com/radiantearth/stac-spec/tree/master/extensions/README.md#extension-maturity):** Proposal
- **Owner**: @pomadchin

This document explains the fields of the Hyperspectral Imagery Extension to a [STAC Item](https://github.com/radiantearth/stac-spec/tree/v1.0.0/item-spec). Items wavelengths information is an important metadata to preserve. Hyperspectral Imagery Extension extends [Electro-Optical Extension Specification](https://github.com/stac-extensions/eo) which handles bands spectral description and adds `hsi:wavelength_min` and `hsi:wavelength_max` Item properties to simplify items search.


- Examples:
  - [Item example](examples/item.json): Shows the basic usage of the extension in a STAC Item
- [JSON Schema](json-schema/schema.json)

## Item Properties and Collection Fields

| Field Name           | Type                      | Description |
| -------------------- | ------------------------- | ----------- |
| hsi:wavelength_min   | \[number]                 | Min center wavelength of the item, in micrometers (μm) |
| hsi:wavelength_max   | \[number]                 | Min center wavelength of the item, in micrometers (μm) |

## Contributing

All contributions are subject to the
[STAC Specification Code of Conduct](https://github.com/radiantearth/stac-spec/blob/master/CODE_OF_CONDUCT.md).
For contributions, please follow the
[STAC specification contributing guide](https://github.com/radiantearth/stac-spec/blob/master/CONTRIBUTING.md) Instructions
for running tests are copied here for convenience.

### Running tests

The same checks that run as checks on PR's are part of the repository and can be run locally to verify that changes are valid. 
To run tests locally, you'll need `npm`, which is a standard part of any [node.js installation](https://nodejs.org/en/download/).

First you'll need to install everything with npm once. Just navigate to the root of this repository and on 
your command line run:
```bash
npm install
```

Then to check markdown formatting and test the examples against the JSON schema, you can run:
```bash
npm test
```

This will spit out the same texts that you see online, and you can then go and fix your markdown or examples.

If the tests reveal formatting problems with the examples, you can fix them with:
```bash
npm run format-examples
```
