# Data card

ActuaryLab AI studies historical French motor third-party liability insurance records, not current Finnish or Nordic insurance business. The original insurer is not named. The upstream description places freMTPL2 approximately in 2011–2013 and says most policies are observed for about one year. A policy's actual recorded exposure, in years, is used; one row is not automatically one exposure-year.

## Provenance and license review

Checked on 15 October 2026:

| Source | Version | OpenML file ID | OpenML-declared license | Source MD5 |
|---|---|---|---|---|
| [freMTPL2freq / 41214](https://www.openml.org/d/41214) | 1 | 20649148 | CC0 | `f8875568bf0ca622929105197e2db613` |
| [freMTPL2sev / 41215](https://www.openml.org/d/41215) | 1 | 20649149 | CC0 | `24cc74449e3931cb1aad0d43a12e7a6e` |

The current metadata endpoints are [41214](https://www.openml.org/api/v1/json/data/41214) and [41215](https://www.openml.org/api/v1/json/data/41215). The downloader records the retrieved metadata, UTC retrieval date, original download URL, and SHA-256 of local original files. Source MD5 identifies OpenML's ARFF originals; it must not be compared to a Parquet rendition as if they were identical byte streams.

Attribution: C. Dutang and A. Charpentier (2018), *CASdatasets: Insurance datasets*. See [CASdatasets](https://github.com/dutangc/CASdatasets), its [freMTPL documentation](https://github.com/dutangc/CASdatasets/blob/master/man/freMTPL.Rd), and *Computational Actuarial Science with R*, edited by Arthur Charpentier.

OpenML declares these particular versions CC0. Separately, the [CASdatasets package DESCRIPTION](https://github.com/dutangc/CASdatasets/blob/master/DESCRIPTION) declares GPL (>= 2). Package licensing and a dataset-specific OpenML declaration are distinct evidence; this project does not claim to settle upstream rights beyond those published statements. To keep redistribution conservative, raw files, policy identifiers, policy rows, fitted estimators and per-policy predictions are excluded from the public repository. The public app uses aggregate JSON and synthetic profiles. The repository's MIT license covers original project code and documentation, not the upstream source datasets. Reusers should check source terms for their own intended use.

## Variables and semantics

The frequency source has `IDpol`, `ClaimNb`, `Exposure`, `VehPower`, `VehAge`, `DrivAge`, `BonusMalus`, `VehBrand`, `VehGas`, `Area`, `Density`, and `Region`. The severity source has `IDpol` and `ClaimAmount`.

- `IDpol` links claim payments to their parent policy; it is not a predictor.
- `ClaimNb` is the source claim count during recorded exposure. A linked positive payment count is a separate derived target.
- `Exposure` is coverage duration in years. Annual frequency is claim count divided by exposure; expected contract-period counts multiply annual frequency by exposure.
- `ClaimAmount` is the recorded cost of a claim, viewed at a later valuation date, rather than a dated complete payment-development history. Values are reported in source monetary units; the project does not silently convert currency or apply inflation adjustment.
- `BonusMalus`, driver and vehicle characteristics, geographic categories and density are historical risk features. Their predictive use does not establish permission to use them in a commercial tariff.

The upstream severity field description calls `IDpol` an occurrence date while the same documentation explicitly uses it to link policy and claim tables. This project follows the documented table relationship and observed identifier matching, flags the inconsistency, and does not infer reliable claim dates from the identifier.

## Coverage, anomalies and limits

The descriptive upstream policy count (677,991) is not substituted for the actual downloaded count. Measured counts, linked/unlinked records, duplicates, claim-count disagreements, nonpositive payments and exposure anomalies are recorded in the generated reconciliation audit; see [DATA_RECONCILIATION.md](DATA_RECONCILIATION.md).

Some claim payments reflect the French IRSA-IDA settlement convention. They are not a pristine sample of unconstrained economic accident losses. The files do not provide a reliable underwriting time series, earned commercial premiums, full coverage terms, expenses, inflation indices or claim development triangles. Random policy holdout estimates are retrospective internal evidence, not prospective pricing validation, reserving evidence, insurer profitability or regulatory capital estimates.
