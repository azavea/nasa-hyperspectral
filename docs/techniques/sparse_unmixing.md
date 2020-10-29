### Problem Description

Linear unmixing can be posed generally using the following equation:

y̅ = Rα̅ + ε

where y̅ is an n- vector giving a sampling of a spectrum with n bands; R is a n×m matrix of reference spectra (endmembers), where the columns are spectra with the same sampling as y̅; α̅ is a vector of abundances for each of the m endmembers; and ε̅ is an n-dimensional random noise term.

One could simply run a linear regression here to determine the abundances, but this will encounter at least the following problems:
1. We are likely to infer extremely small abundances of many substances which may be spurious;
2. we are likely to infer *negative* abundances for some endmembers; and
3. the R matrix consists of columns that may have very small angle separation, and so the OLS normal equations will be ill-conditioned, and thus accuracy will suffer.

We can reframe the problem statement to address (2) by adding constraints:

α̅ ≥0
1ᵗα̅ = 1

where 1ᵗ is the n-dimensional row vector of 1's.  The first constraint is the abundance non-negative constraint (ANC), the second is the abundance sum-to-one constraint (ASC).  The ANC is necessary, the ASC is the matter of some debate, and will not be used in all constrained unmxing strategies.

Given one or both of these constraints, we can focus on problem (1) and obtaining the most meaningful unmixing results.

### Sparse Methods

Sparse regression seeks to minimize the number of nonzero coefficients while providing a good quality fit of the regressand.

A modern example of this method is the *sparse lasso*, which applies a regularization term based on the ℓ₁ norm.  This forces solutions to have only a small number of nonzero coefficients, but comes at the cost of shrinking the nonzero values toward zero.  This is made up for by the fact that solvers are based on quadratic programming techniques which are fast, in contrast to other sparse regression methods.  This method generally does not require the ASC.

Other methods, which may rely on the ASC are basis pursuit, orthogonal matching pursuit, and sparse unmixing by variable splitting and augmented Lagrangian (SUnSAL).

This may be a promising line of investigation if we deem it a worthy investment of time to improve upon already-available unmixing software.

### Annotated Bibliography

> Iordache, Marian-Daniel, José M. Bioucas-Dias, and Antonio Plaza. "[Sparse unmixing of hyperspectral data](http://www.lx.it.pt/~bioucas/files/ieee_tgars_sparse_10.pdf)." *IEEE Transactions on Geoscience and Remote Sensing* 49.6 (2011): 2014-2039.

Nice set up of the problem of unmixing.  Provides a good study of comparative accuracy and performance for several non-lasso methods.  Covers basis pursuit, SUnSAL.

> Iordache, Marian-Daniel, José M. Bioucas-Dias, and Antonio Plaza. "[Collaborative sparse regression for hyperspectral unmixing](http://www.lx.it.pt/~bioucas/files/ieee_tgrs_collaborative_2013.pdf)." *IEEE Transactions on Geoscience and Remote Sensing* 52.1 (2013): 341-354.

Strong paper on the use of lasso for unmixing.  Hundreds of citations.  Good contender for further study.

> Iordache, Marian-Daniel, José M. Bioucas-Dias, and Antonio Plaza. "[Hyperspectral unmixing with sparse group lasso](https://www.researchgate.net/profile/Marian-Daniel_Iordache/publication/220821232_Hyperspectral_unmixingwith_sparse_group_lasso/links/09e4151027d08d909d000000/Hyperspectral-unmixingwith-sparse-group-lasso.pdf)." *2011 IEEE International Geoscience and Remote Sensing Symposium.* IEEE, 2011.

Conference presentation about sparse group lasso for unmixing.  Needs more investigation.
