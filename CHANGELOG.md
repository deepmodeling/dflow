# CHANGELOG

## [1.8.86](https://github.com/deepmodeling/dflow/compare/v1.8.85...v1.8.86) (2024-08-07)


### Bug Fixes

* multiprocessing in debug mode ([fe6fdd2](https://github.com/deepmodeling/dflow/commit/fe6fdd21089baf1684f87ec20a4e948dc4e2086b))

## [1.8.85](https://github.com/deepmodeling/dflow/compare/v1.8.84...v1.8.85) (2024-08-06)


### Bug Fixes

* handle sub_path slices of artifact list for debug mode ([0d9e1a0](https://github.com/deepmodeling/dflow/commit/0d9e1a0ba3790e930d5cead16acd2b24f1720af2))
* unpicklable function OP in debug mode ([0d9e1a0](https://github.com/deepmodeling/dflow/commit/0d9e1a0ba3790e930d5cead16acd2b24f1720af2))

## [1.8.84](https://github.com/deepmodeling/dflow/compare/v1.8.83...v1.8.84) (2024-08-05)


### Bug Fixes

* copy scope before submit ([1fb7293](https://github.com/deepmodeling/dflow/commit/1fb7293e4d301dca00b97b5d3c93808adf1a1d59))

## [1.8.83](https://github.com/deepmodeling/dflow/compare/v1.8.82...v1.8.83) (2024-08-05)


### Bug Fixes

* modify self after all processes have finished to avoid competition ([f542d3f](https://github.com/deepmodeling/dflow/commit/f542d3fef982f1ddfc9a6a392d5dfc1b7f452439))

## [1.8.82](https://github.com/deepmodeling/dflow/compare/v1.8.81...v1.8.82) (2024-08-02)


### Bug Fixes

* subprocesses only return phase, output parameter values and output artifact paths ([778c948](https://github.com/deepmodeling/dflow/commit/778c94846af43eb8ab00ef57d60a5782f8b5cd87))

## [1.8.81](https://github.com/deepmodeling/dflow/compare/v1.8.80...v1.8.81) (2024-08-02)


### Bug Fixes

* do not deepcopy outputs of subprocesses ([7d0816a](https://github.com/deepmodeling/dflow/commit/7d0816a1e294b9673ec4f128f63fcc41edc5c7ae))

## [1.8.80](https://github.com/deepmodeling/dflow/compare/v1.8.79...v1.8.80) (2024-07-30)


### Bug Fixes

* debug: optional artifact from output artifact ([925aee9](https://github.com/deepmodeling/dflow/commit/925aee946c6ee4feacbbcf839fd5e5916a652b62))
* debug: optional output artifact ([925aee9](https://github.com/deepmodeling/dflow/commit/925aee946c6ee4feacbbcf839fd5e5916a652b62))
* debug: wait for the download to complete ([925aee9](https://github.com/deepmodeling/dflow/commit/925aee946c6ee4feacbbcf839fd5e5916a652b62))

## [1.8.79](https://github.com/deepmodeling/dflow/compare/v1.8.78...v1.8.79) (2024-07-29)


### Bug Fixes

* override inferred dependencies if specified explicitly for task ([d312dfe](https://github.com/deepmodeling/dflow/commit/d312dfef33b6067e02c1bdebd48444e4a1c5a427))
* render item for super OP ([d312dfe](https://github.com/deepmodeling/dflow/commit/d312dfef33b6067e02c1bdebd48444e4a1c5a427))

## [1.8.78](https://github.com/deepmodeling/dflow/compare/v1.8.77...v1.8.78) (2024-07-16)


### Bug Fixes

* add DFLOW_TEMPDIR ([efaa966](https://github.com/deepmodeling/dflow/commit/efaa966e49b6e2fef1204172e48b8e2f8c931e23))

## [1.8.77](https://github.com/deepmodeling/dflow/compare/v1.8.76...v1.8.77) (2024-06-06)


### Bug Fixes

* add pool_timeout to Slices ([c1de9b1](https://github.com/deepmodeling/dflow/commit/c1de9b13e7f046347e2dd184b96b934080104fe5))

## [1.8.76](https://github.com/deepmodeling/dflow/compare/v1.8.75...v1.8.76) (2024-06-06)


### Bug Fixes

* add merge_bohrium_job_group to dispatcher executor ([90d8f99](https://github.com/deepmodeling/dflow/commit/90d8f9969c405280baa61d780618eb0271e37b60))

## [1.8.75](https://github.com/deepmodeling/dflow/compare/v1.8.74...v1.8.75) (2024-06-05)


### Bug Fixes

* key and group_size for merge_sliced_step ([3fec184](https://github.com/deepmodeling/dflow/commit/3fec184be23949792ca68cd07234c9111d30c15c))

## [1.8.74](https://github.com/deepmodeling/dflow/compare/v1.8.73...v1.8.74) (2024-06-05)


### Bug Fixes

* set save_keys_in_global_outputs to False by default ([192db78](https://github.com/deepmodeling/dflow/commit/192db78d4bf1e7ad275ebe3b7e0fa619d2d20083))

## [1.8.73](https://github.com/deepmodeling/dflow/compare/v1.8.72...v1.8.73) (2024-06-01)


### Bug Fixes

* support group_size for subpath mode of slices ([c43da1a](https://github.com/deepmodeling/dflow/commit/c43da1a47bb312bc0d25a363d8550d9defa0017e))

## [1.8.72](https://github.com/deepmodeling/dflow/compare/v1.8.71...v1.8.72) (2024-05-30)


### Bug Fixes

* `op.function` doesn't work with slices. ([7dec8b9](https://github.com/deepmodeling/dflow/commit/7dec8b9c12863096be5b5ea9b89595ae4bbc4cbc))
* override None item in assembling path object from artifact catalog ([ecb544f](https://github.com/deepmodeling/dflow/commit/ecb544f62a05efe0cf12aeee9a2d225887c2b417))

## [1.8.71](https://github.com/deepmodeling/dflow/compare/v1.8.70...v1.8.71) (2024-05-29)


### Bug Fixes

* pass on sliced big parameter for sliced super OP ([a2e1867](https://github.com/deepmodeling/dflow/commit/a2e1867843788fe2fb65c6f1aeffa5b5e06aac66))

## [1.8.70](https://github.com/deepmodeling/dflow/compare/v1.8.69...v1.8.70) (2024-05-29)


### Bug Fixes

* BigParameter(str) in debug mode ([b4f5452](https://github.com/deepmodeling/dflow/commit/b4f54523f5d11d52f2a9e44205c0cc0f892a4162))

## [1.8.69](https://github.com/deepmodeling/dflow/compare/v1.8.68...v1.8.69) (2024-05-28)


### Bug Fixes

* BigParameter(str) in debug mode ([9294c4a](https://github.com/deepmodeling/dflow/commit/9294c4a70675b1a8ed21767cddc06c84836647e3))

## [1.8.68](https://github.com/deepmodeling/dflow/compare/v1.8.67...v1.8.68) (2024-05-28)


### Bug Fixes

* handle sliced recursive super OP with skip_slice_input ([aa530dc](https://github.com/deepmodeling/dflow/commit/aa530dc3fd69367d83f761290989958579739326))

## [1.8.67](https://github.com/deepmodeling/dflow/compare/v1.8.66...v1.8.67) (2024-05-24)


### Bug Fixes

* add dispatcher_debug ([a4eeb69](https://github.com/deepmodeling/dflow/commit/a4eeb69ad88426c9034780e15187bd225e7141a2))

## [1.8.66](https://github.com/deepmodeling/dflow/compare/v1.8.65...v1.8.66) (2024-05-23)


### Bug Fixes

* get exit code explicitly for Bohrium with dispatcher ([568237c](https://github.com/deepmodeling/dflow/commit/568237c7a730442766d9697cc2ebd13bc6c65bcb))

## [1.8.65](https://github.com/deepmodeling/dflow/compare/v1.8.64...v1.8.65) (2024-05-18)


### Bug Fixes

* add switch raise_for_group ([ca77068](https://github.com/deepmodeling/dflow/commit/ca770681b9e6f7459fbb5476868f0bcf20cf544c))

## [1.8.64](https://github.com/deepmodeling/dflow/compare/v1.8.63...v1.8.64) (2024-04-30)


### Bug Fixes

* handle reused artifacts for slices of slices ([107e6db](https://github.com/deepmodeling/dflow/commit/107e6dbdd4acb7e3c00ff6d8242f861e82412a19))

## [1.8.63](https://github.com/deepmodeling/dflow/compare/v1.8.62...v1.8.63) (2024-04-30)


### Bug Fixes

* handle reused artifacts for slices of slices ([0e6dad9](https://github.com/deepmodeling/dflow/commit/0e6dad9ee3ae4d2453fbed15ce57043a4d497ea5))

## [1.8.62](https://github.com/deepmodeling/dflow/compare/v1.8.61...v1.8.62) (2024-04-12)


### Bug Fixes

* downgrade to full query when key(s) not found in the global outputs in query_step_by_key ([cf2156b](https://github.com/deepmodeling/dflow/commit/cf2156b1c8384fad1a78c724ba7ff4d7aa4c7c2a))
* update key-ID map in global outputs according to the new workflow ID when reusing ([cf2156b](https://github.com/deepmodeling/dflow/commit/cf2156b1c8384fad1a78c724ba7ff4d7aa4c7c2a))

## [1.8.61](https://github.com/deepmodeling/dflow/compare/v1.8.60...v1.8.61) (2024-04-07)


### Bug Fixes

* add keys=True to jsonpickle ([3a0b4de](https://github.com/deepmodeling/dflow/commit/3a0b4de1a4cd7355ff47a1074709886341e024ce))

## [1.8.60](https://github.com/deepmodeling/dflow/compare/v1.8.59...v1.8.60) (2024-04-01)


### Bug Fixes

* add prefix when upload_s3 with key ([fed4697](https://github.com/deepmodeling/dflow/commit/fed46970d5271338575b7cccd21fa8027b0fea5e))

## [1.8.59](https://github.com/deepmodeling/dflow/compare/v1.8.58...v1.8.59) (2024-04-01)


### Bug Fixes

* object of type Path has no len() in upload_s3 ([8ca08f4](https://github.com/deepmodeling/dflow/commit/8ca08f48c0e6c7f23f1b57480c45ee736ac851d1))
* race condition in merging outputs in debug mode ([8ca08f4](https://github.com/deepmodeling/dflow/commit/8ca08f48c0e6c7f23f1b57480c45ee736ac851d1))

## [1.8.58](https://github.com/deepmodeling/dflow/compare/v1.8.57...v1.8.58) (2024-03-29)


### Bug Fixes

* opt multi-merge ([dd89130](https://github.com/deepmodeling/dflow/commit/dd891309ca4f15e691dfbf8ced100a3a8c419ae2))

## [1.8.57](https://github.com/deepmodeling/dflow/compare/v1.8.56...v1.8.57) (2024-03-28)


### Bug Fixes

* multi-merge case when key is not used ([74e1bd8](https://github.com/deepmodeling/dflow/commit/74e1bd826874e485463cdf6a0e291f03f42c7d0b))

## [1.8.56](https://github.com/deepmodeling/dflow/compare/v1.8.55...v1.8.56) (2024-03-26)


### Bug Fixes

* add BOHRIUM_UPLOAD_PROGRESS ([0f2f823](https://github.com/deepmodeling/dflow/commit/0f2f823f6c972b5e03da847220fb2c6564eb871d))

## [1.8.55](https://github.com/deepmodeling/dflow/compare/v1.8.54...v1.8.55) (2024-03-18)


### Bug Fixes

* format ([fbf5725](https://github.com/deepmodeling/dflow/commit/fbf5725e40aec464a3b5a8df9ee1e93b7097fb4b))
* reuse global outputs of reused steps ([751b1f4](https://github.com/deepmodeling/dflow/commit/751b1f4a159dc069b99ba140aef8feba8a46e062))
* support create_slice_dir when pool_size is used ([f8bb80c](https://github.com/deepmodeling/dflow/commit/f8bb80c70d4fdfd881c9b89617f2f0526603bc11))

## [1.8.54](https://github.com/deepmodeling/dflow/compare/v1.8.53...v1.8.54) (2024-03-04)


### Bug Fixes

* get create_dir from slices ([e96be1e](https://github.com/deepmodeling/dflow/commit/e96be1ea7a6f849eaa9f9fcea24afe173487c9fe))

## [1.8.53](https://github.com/deepmodeling/dflow/compare/v1.8.52...v1.8.53) (2024-03-04)


### Bug Fixes

* add create_dir to slices ([74c6409](https://github.com/deepmodeling/dflow/commit/74c64098cad0393cafe89fdb5cd610efdfc74abe))

## [1.8.52](https://github.com/deepmodeling/dflow/compare/v1.8.51...v1.8.52) (2024-02-28)


### Bug Fixes

* fix run_command ([a86753f](https://github.com/deepmodeling/dflow/commit/a86753f14dbcf153ce4fbc664521ce5c2005e738))
* print_oe in run_command ([d7e424e](https://github.com/deepmodeling/dflow/commit/d7e424e26859cb6b7933d358c99cb3c968e7ccda))

## [1.8.51](https://github.com/deepmodeling/dflow/compare/v1.8.50...v1.8.51) (2024-02-23)


### Bug Fixes

* add debug_save_copy_method ([6ab8973](https://github.com/deepmodeling/dflow/commit/6ab89735c3edcf319d02cced4bea47894fbe73b7))

## [1.8.50](https://github.com/deepmodeling/dflow/compare/v1.8.49...v1.8.50) (2024-02-22)


### Bug Fixes

* failfast=False for default in debug mode ([ac2c5a9](https://github.com/deepmodeling/dflow/commit/ac2c5a9a21b1e315c62f77b8f8e011634a431596))

## [1.8.49](https://github.com/deepmodeling/dflow/compare/v1.8.48...v1.8.49) (2024-02-22)


### Bug Fixes

* support wf.query() in debug mode ([a66ba11](https://github.com/deepmodeling/dflow/commit/a66ba11e55c1c81ab40769675bd91f4199cedd2d))

## [1.8.48](https://github.com/deepmodeling/dflow/compare/v1.8.47...v1.8.48) (2024-02-13)


### Bug Fixes

* merge output artifacts for slices of recursive steps ([53c902e](https://github.com/deepmodeling/dflow/commit/53c902e06de2f6d965c60f0970a8e69bd56db220))

## [1.8.47](https://github.com/deepmodeling/dflow/compare/v1.8.46...v1.8.47) (2024-02-08)


### Bug Fixes

* slices for recursive steps ([c62c0c6](https://github.com/deepmodeling/dflow/commit/c62c0c6f5022a97e42066a2fcc3376b11861f85d))

## [1.8.46](https://github.com/deepmodeling/dflow/compare/v1.8.45...v1.8.46) (2024-02-06)


### Bug Fixes

* specify storage location of a file in debug mode ([b4d7257](https://github.com/deepmodeling/dflow/commit/b4d725764db0ecdead2c6aabc91b490b0f6decb5))

## [1.8.45](https://github.com/deepmodeling/dflow/compare/v1.8.44...v1.8.45) (2024-01-15)


### Bug Fixes

* add label to memoize config map ([5800f2a](https://github.com/deepmodeling/dflow/commit/5800f2a904a727d313ad0c80654b655b973d1418))
* retry for status 5xx of query API ([5800f2a](https://github.com/deepmodeling/dflow/commit/5800f2a904a727d313ad0c80654b655b973d1418))

## [1.8.44](https://github.com/deepmodeling/dflow/compare/v1.8.43...v1.8.44) (2024-01-05)


### Bug Fixes

* dictionary changed size during iteration ([eba3d14](https://github.com/deepmodeling/dflow/commit/eba3d14b927558777cc0536607e9cf5c5bedaa3e))

## [1.8.43](https://github.com/deepmodeling/dflow/compare/v1.8.42...v1.8.43) (2024-01-05)


### Bug Fixes

* add debug messages for process pool executor ([0dab022](https://github.com/deepmodeling/dflow/commit/0dab0220ed3b6d89635d9ba308f36c153db6ff23))

## [1.8.42](https://github.com/deepmodeling/dflow/compare/v1.8.41...v1.8.42) (2024-01-04)


### Bug Fixes

* use lock to avoid redundant downloads ([e654919](https://github.com/deepmodeling/dflow/commit/e6549190892b65c9e985e61aea135e5e1417e3d8))

## [1.8.41](https://github.com/deepmodeling/dflow/compare/v1.8.40...v1.8.41) (2024-01-03)


### Bug Fixes

* optimize worker number ([c34f122](https://github.com/deepmodeling/dflow/commit/c34f1226d4b7f106147508ed18a282e158b112ec))

## [1.8.40](https://github.com/deepmodeling/dflow/compare/v1.8.39...v1.8.40) (2023-12-29)


### Bug Fixes

* File name too long in downloading HTTP artifact ([2fab9bc](https://github.com/deepmodeling/dflow/commit/2fab9bc0f08859f1a35e28539b436e58740958c3))

## [1.8.39](https://github.com/deepmodeling/dflow/compare/v1.8.38...v1.8.39) (2023-12-27)


### Bug Fixes

* argo enumerate in debug mode ([fdadc15](https://github.com/deepmodeling/dflow/commit/fdadc155633c105ebb2a035bd8e030c639c548db))

## [1.8.38](https://github.com/deepmodeling/dflow/compare/v1.8.37...v1.8.38) (2023-12-27)


### Bug Fixes

* sprig.fromJson in debug mode ([27cde52](https://github.com/deepmodeling/dflow/commit/27cde522ff9f4bd7d7bfe6ff901c82e61a4d6a3a))

## [1.8.37](https://github.com/deepmodeling/dflow/compare/v1.8.36...v1.8.37) (2023-12-27)


### Bug Fixes

* replace jsonpath and string with python functions ([72b5d49](https://github.com/deepmodeling/dflow/commit/72b5d49fdaf0fefdd1de845f023efbcaada2206b))

## [1.8.36](https://github.com/deepmodeling/dflow/compare/v1.8.35...v1.8.36) (2023-12-26)


### Bug Fixes

* render expr with {{= ([d31a51b](https://github.com/deepmodeling/dflow/commit/d31a51be3b0ebd6060d133fca5fb360c37ff5e3d))

## [1.8.35](https://github.com/deepmodeling/dflow/compare/v1.8.34...v1.8.35) (2023-12-22)


### Bug Fixes

* a bug of enumerate in debug mode ([fae33c3](https://github.com/deepmodeling/dflow/commit/fae33c3fe81581960eced0b6386f40b66acad024))

## [1.8.34](https://github.com/deepmodeling/dflow/compare/v1.8.33...v1.8.34) (2023-12-21)


### Bug Fixes

* bug of argo enumerate in debug mode ([54ac7ae](https://github.com/deepmodeling/dflow/commit/54ac7ae8c00409e794c638b93ceba83d75308217))

## [1.8.33](https://github.com/deepmodeling/dflow/compare/v1.8.32...v1.8.33) (2023-12-21)


### Bug Fixes

* item_list is not a list ([d48e489](https://github.com/deepmodeling/dflow/commit/d48e4892c4c0b18b52efbb745f8c355cb58e0713))
* pass context to steps ([d48e489](https://github.com/deepmodeling/dflow/commit/d48e4892c4c0b18b52efbb745f8c355cb58e0713))

## [1.8.32](https://github.com/deepmodeling/dflow/compare/v1.8.31...v1.8.32) (2023-12-20)


### Bug Fixes

* default value of output parameter in debug mode ([8ed6e9e](https://github.com/deepmodeling/dflow/commit/8ed6e9e098653ee9f58cb19c6919a92c3c5c4dc7))

## [1.8.31](https://github.com/deepmodeling/dflow/compare/v1.8.30...v1.8.31) (2023-12-20)


### Bug Fixes

* value_from_parameter without {{}} ([53585e0](https://github.com/deepmodeling/dflow/commit/53585e0271af2b658f65c0b88c5c76cc950257d1))

## [1.8.30](https://github.com/deepmodeling/dflow/compare/v1.8.29...v1.8.30) (2023-12-20)


### Bug Fixes

* singularity exec instead of singularity run ([b80a948](https://github.com/deepmodeling/dflow/commit/b80a9488a343237a4e6d41963840c74bcc1ac42d))

## [1.8.29](https://github.com/deepmodeling/dflow/compare/v1.8.28...v1.8.29) (2023-12-19)


### Bug Fixes

* parse argo enumerate expression in debug mode ([a9457ea](https://github.com/deepmodeling/dflow/commit/a9457eae86923b1b6ee565d1b71d7bfdfa0c74a6))

## [1.8.28](https://github.com/deepmodeling/dflow/compare/v1.8.27...v1.8.28) (2023-12-19)


### Bug Fixes

* container mount nonexist tmp ([bea5ac2](https://github.com/deepmodeling/dflow/commit/bea5ac21a0d2b64d90b27c8611cf454026724422))
* modify merged output artifact ([bea5ac2](https://github.com/deepmodeling/dflow/commit/bea5ac21a0d2b64d90b27c8611cf454026724422))

## [1.8.27](https://github.com/deepmodeling/dflow/compare/v1.8.26...v1.8.27) (2023-11-27)


### Bug Fixes

* missing dependencies of init-artifact for sub-path sliced task ([6d4a81d](https://github.com/deepmodeling/dflow/commit/6d4a81d091034e730e068edc86de14841142263e))

## [1.8.26](https://github.com/deepmodeling/dflow/compare/v1.8.25...v1.8.26) (2023-11-23)


### Bug Fixes

* support optional output artifact without from/path specified ([6211ebd](https://github.com/deepmodeling/dflow/commit/6211ebd53048bc41802bb315b8a3a9e6d1c0ce7c))

## [1.8.25](https://github.com/deepmodeling/dflow/compare/v1.8.24...v1.8.25) (2023-11-22)


### Bug Fixes

* parse type in yaml ([847251f](https://github.com/deepmodeling/dflow/commit/847251f33f29d65b7cccd91f2533700f11ae7248))
* subpath when parsing yaml ([847251f](https://github.com/deepmodeling/dflow/commit/847251f33f29d65b7cccd91f2533700f11ae7248))
* with_param in debug mode ([847251f](https://github.com/deepmodeling/dflow/commit/847251f33f29d65b7cccd91f2533700f11ae7248))

## [1.8.24](https://github.com/deepmodeling/dflow/compare/v1.8.23...v1.8.24) (2023-11-20)


### Bug Fixes

* backward compatibility ([fbcecab](https://github.com/deepmodeling/dflow/commit/fbcecab0446f57b5b90944ca84c6af5a6eaf8063))
* We need not input artifact path for a step ([9374e2a](https://github.com/deepmodeling/dflow/commit/9374e2a3bc9e65ea52c35ca459dea90eafd5d093))

## [1.8.23](https://github.com/deepmodeling/dflow/compare/v1.8.22...v1.8.23) (2023-11-17)


### Bug Fixes

* support retry multiple steps in a workflow ([cf97746](https://github.com/deepmodeling/dflow/commit/cf9774622ab28c657ceca41456e6b240911fc20b))

## [1.8.22](https://github.com/deepmodeling/dflow/compare/v1.8.21...v1.8.22) (2023-11-14)


### Bug Fixes

* add retry for query response 500 ([02f2467](https://github.com/deepmodeling/dflow/commit/02f2467f12a92a1816c252115f151ef10cb40df4))

## [1.8.21](https://github.com/deepmodeling/dflow/compare/v1.8.20...v1.8.21) (2023-11-09)


### Bug Fixes

* cwd is / ([02a8c76](https://github.com/deepmodeling/dflow/commit/02a8c76cfba7277c89a2b1fddd68d478230e7b81))

## [1.8.20](https://github.com/deepmodeling/dflow/compare/v1.8.19...v1.8.20) (2023-11-09)


### Bug Fixes

* add envs to DispatcherExecutor ([df1c9c4](https://github.com/deepmodeling/dflow/commit/df1c9c441f57d7a0edecbdc5d62c4689a86dc45a))

## [1.8.19](https://github.com/deepmodeling/dflow/compare/v1.8.18...v1.8.19) (2023-11-04)


### Bug Fixes

* path problem in try_to_execute ([1d6fe6e](https://github.com/deepmodeling/dflow/commit/1d6fe6ee3b5301d5631c3bb9181c630136a60dbe))
* set_directory ([1d6fe6e](https://github.com/deepmodeling/dflow/commit/1d6fe6ee3b5301d5631c3bb9181c630136a60dbe))

## [1.8.18](https://github.com/deepmodeling/dflow/compare/v1.8.17...v1.8.18) (2023-10-31)


### Bug Fixes

* add option id when querying archived workflows ([a723874](https://github.com/deepmodeling/dflow/commit/a723874ce229d3bcc09fcd295f98fc467253e702))
* stuck when exiting ProcessPoolExecutor ([a723874](https://github.com/deepmodeling/dflow/commit/a723874ce229d3bcc09fcd295f98fc467253e702))

## [1.8.17](https://github.com/deepmodeling/dflow/compare/v1.8.16...v1.8.17) (2023-10-26)


### Bug Fixes

* outputs has no attribute artifacts (for argo&lt;3.4) ([e85800b](https://github.com/deepmodeling/dflow/commit/e85800b25189803a80f165f8bc1e41c3a736c1bf))

## [1.8.16](https://github.com/deepmodeling/dflow/compare/v1.8.15...v1.8.16) (2023-10-24)


### Bug Fixes

* add dflow/python/vendor/typeguard to packages in setup.py ([35663ef](https://github.com/deepmodeling/dflow/commit/35663ef848be35e3062e46decfdaf3dfef2164a5))
* add unittest to github actions ([a7fa89d](https://github.com/deepmodeling/dflow/commit/a7fa89d88c24474899805acf33a507de3a0ac6a6))
* noqa for typeguard ([cacb2cf](https://github.com/deepmodeling/dflow/commit/cacb2cf631d9669bb7003421ad9f2fa3c93f982f))
* rename _vendor -&gt; vendor ([9c3a5bf](https://github.com/deepmodeling/dflow/commit/9c3a5bf7e1c68b0e5b26bbf4a98e421e4b05a860))
* vendor typeguard==2.13.3 ([a7fa89d](https://github.com/deepmodeling/dflow/commit/a7fa89d88c24474899805acf33a507de3a0ac6a6))

## [1.8.15](https://github.com/deepmodeling/dflow/compare/v1.8.14...v1.8.15) (2023-10-18)


### Bug Fixes

* cd to workdir before execute for grouped slices ([a880d76](https://github.com/deepmodeling/dflow/commit/a880d762f73964e61b55bc4be83fe0e9a3ed8e1b))

## [1.8.14](https://github.com/deepmodeling/dflow/compare/v1.8.13...v1.8.14) (2023-10-17)


### Bug Fixes

* private_key_file of DispatcherExecutor in debug mode ([30ee41c](https://github.com/deepmodeling/dflow/commit/30ee41cc68649c42031d9014d79700dc83088f89))

## [1.8.13](https://github.com/deepmodeling/dflow/compare/v1.8.12...v1.8.13) (2023-10-16)


### Bug Fixes

* list has no attribute inputs ([196cefe](https://github.com/deepmodeling/dflow/commit/196cefe45a3adef8484369ed25f18691aecd7deb))
* remove unnecessary __getstate__/__setstate__ methods ([196cefe](https://github.com/deepmodeling/dflow/commit/196cefe45a3adef8484369ed25f18691aecd7deb))

## [1.8.12](https://github.com/deepmodeling/dflow/compare/v1.8.11...v1.8.12) (2023-10-14)


### Bug Fixes

* remove __getstate__ and __setstate__ methods of ArgoSequence ([423d44f](https://github.com/deepmodeling/dflow/commit/423d44f504caba0c3a110b5ed34e50883b5322e3))

## [1.8.11](https://github.com/deepmodeling/dflow/compare/v1.8.10...v1.8.11) (2023-10-14)


### Bug Fixes

* race condition of removing symlink of global outputs in debug mode ([b9f004e](https://github.com/deepmodeling/dflow/commit/b9f004e8d5389c86b12c63569982c4b72fac506f))

## [1.8.10](https://github.com/deepmodeling/dflow/compare/v1.8.9...v1.8.10) (2023-10-07)


### Bug Fixes

* depends on check_step if check_step is not None ([1d40655](https://github.com/deepmodeling/dflow/commit/1d4065513b51c451aacffdd9fa78514551113d2e))

## [1.8.9](https://github.com/deepmodeling/dflow/compare/v1.8.8...v1.8.9) (2023-10-07)


### Bug Fixes

* check task depends on task finish ([2a166b5](https://github.com/deepmodeling/dflow/commit/2a166b545bb730068705d88589dcea3050373f27))

## [1.8.8](https://github.com/deepmodeling/dflow/compare/v1.8.7...v1.8.8) (2023-10-07)


### Bug Fixes

* dispatcher pod use ephemeral storage currently, do not remove ephemeral-storage in requests/limits in dispatcher executor ([5015d06](https://github.com/deepmodeling/dflow/commit/5015d06870b59850834821ef5990913414235ea7))

## [1.8.7](https://github.com/deepmodeling/dflow/compare/v1.8.6...v1.8.7) (2023-10-07)


### Bug Fixes

* not modify list of dataset artifacts when set artifacts ([cbe42bb](https://github.com/deepmodeling/dflow/commit/cbe42bb523d901b91217d3b53a3af941f6ceb89d))

## [1.8.6](https://github.com/deepmodeling/dflow/compare/v1.8.5...v1.8.6) (2023-10-06)


### Bug Fixes

* removeprefix and removesuffix only supported for python&gt;=3.9 ([8f34e59](https://github.com/deepmodeling/dflow/commit/8f34e598b3b4a81ff91c9718cffd8e34b851d40d))

## [1.8.5](https://github.com/deepmodeling/dflow/compare/v1.8.4...v1.8.5) (2023-09-28)


### Bug Fixes

* remove scheduling strategies in dispatcher executor ([e021874](https://github.com/deepmodeling/dflow/commit/e021874593ab0728f2660c4c0352585d4e453195))

## [1.8.4](https://github.com/deepmodeling/dflow/compare/v1.8.3...v1.8.4) (2023-09-27)


### Bug Fixes

* add optional to output artifact ([6f7979c](https://github.com/deepmodeling/dflow/commit/6f7979c662c5070e66a6c43fdd5a4016668bea66))

## [1.8.3](https://github.com/deepmodeling/dflow/compare/v1.8.2...v1.8.3) (2023-09-27)


### Bug Fixes

* support continue_on for Task ([4cc4f9c](https://github.com/deepmodeling/dflow/commit/4cc4f9c5c035d3cffad2e98533a7d2b726c64d29))

## [1.8.2](https://github.com/deepmodeling/dflow/compare/v1.8.1...v1.8.2) (2023-09-26)


### Bug Fixes

* add codegen ([3278ef8](https://github.com/deepmodeling/dflow/commit/3278ef808f9669f5b3cc93e4a603bd314efa537e))

## [1.8.1](https://github.com/deepmodeling/dflow/compare/v1.8.0...v1.8.1) (2023-09-25)


### Bug Fixes

* dflow graph for function OP ([d60099f](https://github.com/deepmodeling/dflow/commit/d60099f92dfcf78703b5046e20dae873659974e8))
* refer to parameters with {{inputs.parameters.xxx}} in dflow graph ([d60099f](https://github.com/deepmodeling/dflow/commit/d60099f92dfcf78703b5046e20dae873659974e8))

## [1.8.0](https://github.com/deepmodeling/dflow/compare/v1.7.86...v1.8.0) (2023-09-23)


### Features

* make workflows jsonizable ([6fbfb23](https://github.com/deepmodeling/dflow/commit/6fbfb23d3720923c316decdfbb4953374fd6ec32))

## [1.7.86](https://github.com/deepmodeling/dflow/compare/v1.7.85...v1.7.86) (2023-09-21)


### Bug Fixes

* optional artifact when grouping slices ([ce9361d](https://github.com/deepmodeling/dflow/commit/ce9361d747ebcb609066a7baf5cc03acdcefa2ca))

## [1.7.85](https://github.com/deepmodeling/dflow/compare/v1.7.84...v1.7.85) (2023-09-20)


### Bug Fixes

* convert project_id to int ([eabe7e1](https://github.com/deepmodeling/dflow/commit/eabe7e1eb41c08a1fd5f9f1e04fbfce02722aa29))

## [1.7.84](https://github.com/deepmodeling/dflow/compare/v1.7.83...v1.7.84) (2023-09-20)


### Bug Fixes

* project_id -&gt; projectId ([05b4731](https://github.com/deepmodeling/dflow/commit/05b473142efeb6cce4c9b6a88aba8a804b894ec3))

## [1.7.83](https://github.com/deepmodeling/dflow/compare/v1.7.82...v1.7.83) (2023-09-16)


### Bug Fixes

* add convert_to_graph ([54573e5](https://github.com/deepmodeling/dflow/commit/54573e50423a6b7d19776e6d4dc7a92f8e6d4b1e))
* add debug_workdir ([88c4a77](https://github.com/deepmodeling/dflow/commit/88c4a771ff67bf3051b8a4bf56bb51977c1ca711))
* recursive symlink ([88c4a77](https://github.com/deepmodeling/dflow/commit/88c4a771ff67bf3051b8a4bf56bb51977c1ca711))
* str(str) ([88c4a77](https://github.com/deepmodeling/dflow/commit/88c4a771ff67bf3051b8a4bf56bb51977c1ca711))

## [1.7.82](https://github.com/deepmodeling/dflow/compare/v1.7.81...v1.7.82) (2023-09-14)


### Bug Fixes

* update workflow with patch ([c734c24](https://github.com/deepmodeling/dflow/commit/c734c24bff3c1da4ff9dde6a7360946b9b783a70))

## [1.7.81](https://github.com/deepmodeling/dflow/compare/v1.7.80...v1.7.81) (2023-09-12)


### Bug Fixes

* add tolerations to template ([b8a5a29](https://github.com/deepmodeling/dflow/commit/b8a5a292942ed39beb3bba9d9f5f905bb2a5655c))

## [1.7.80](https://github.com/deepmodeling/dflow/compare/v1.7.79...v1.7.80) (2023-09-11)


### Bug Fixes

* dflow download command ([23c6231](https://github.com/deepmodeling/dflow/commit/23c6231ed324e14bc934c32603c17af44c208750))
* success ratio for grouped slices ([23c6231](https://github.com/deepmodeling/dflow/commit/23c6231ed324e14bc934c32603c17af44c208750))

## [1.7.79](https://github.com/deepmodeling/dflow/compare/v1.7.78...v1.7.79) (2023-09-05)


### Bug Fixes

* subpath slices for steps ([f4ad94b](https://github.com/deepmodeling/dflow/commit/f4ad94b54f52d34dd0946c27be04f739d897e211))

## [1.7.78](https://github.com/deepmodeling/dflow/compare/v1.7.77...v1.7.78) (2023-09-05)


### Bug Fixes

* support subpath slices for steps ([a77f1e4](https://github.com/deepmodeling/dflow/commit/a77f1e47f75dabe92c616a120acf28429e958fae))

## [1.7.77](https://github.com/deepmodeling/dflow/compare/v1.7.76...v1.7.77) (2023-08-31)


### Bug Fixes

* remove Certificate and Issuer in manifest ([dd4420a](https://github.com/deepmodeling/dflow/commit/dd4420a6ea417516a8b952bd09eb9bee460e7107))
* support for group of parallel steps/dag in debug mode ([dd4420a](https://github.com/deepmodeling/dflow/commit/dd4420a6ea417516a8b952bd09eb9bee460e7107))

## [1.7.76](https://github.com/deepmodeling/dflow/compare/v1.7.75...v1.7.76) (2023-08-30)


### Bug Fixes

* avoid to terminate parent process in terminating workflow in debug mode ([50b864e](https://github.com/deepmodeling/dflow/commit/50b864e0e9460e2f8d322be484ea8271380b6469))

## [1.7.75](https://github.com/deepmodeling/dflow/compare/v1.7.74...v1.7.75) (2023-08-29)


### Bug Fixes

* add quick-start-postgres-3.4.1-deepmodeling.yaml ([31c3fc2](https://github.com/deepmodeling/dflow/commit/31c3fc26723c4b168743223568edf1e0fa0739ce))
* raise FileNotFoundError in upload_s3 ([31c3fc2](https://github.com/deepmodeling/dflow/commit/31c3fc26723c4b168743223568edf1e0fa0739ce))
* support function OP for python 3.6 ([453e999](https://github.com/deepmodeling/dflow/commit/453e9992ad2d30b9b14670a5a18913e995ff3b55))

## [1.7.74](https://github.com/deepmodeling/dflow/compare/v1.7.73...v1.7.74) (2023-08-27)


### Bug Fixes

* add debug_artifact_dir ([7046692](https://github.com/deepmodeling/dflow/commit/70466922599b0ea40c4aa4a9e5a0a863b42ebb83))
* bug in optional artifact in debug mode ([7046692](https://github.com/deepmodeling/dflow/commit/70466922599b0ea40c4aa4a9e5a0a863b42ebb83))
* reconstruct download artifact in debug mode ([7046692](https://github.com/deepmodeling/dflow/commit/70466922599b0ea40c4aa4a9e5a0a863b42ebb83))
* upload_s3 in debug mode ([7046692](https://github.com/deepmodeling/dflow/commit/70466922599b0ea40c4aa4a9e5a0a863b42ebb83))

## [1.7.73](https://github.com/deepmodeling/dflow/compare/v1.7.72...v1.7.73) (2023-08-25)


### Bug Fixes

* merge dir in debug mode ([7129ff2](https://github.com/deepmodeling/dflow/commit/7129ff2daab273f99b955fd61f0f26b0fd540954))

## [1.7.72](https://github.com/deepmodeling/dflow/compare/v1.7.71...v1.7.72) (2023-08-25)


### Bug Fixes

* write pid to pod dir in debug mode ([c0b39d1](https://github.com/deepmodeling/dflow/commit/c0b39d1e9c389efed3f2e6921492c028caf52e15))

## [1.7.71](https://github.com/deepmodeling/dflow/compare/v1.7.70...v1.7.71) (2023-08-25)


### Bug Fixes

* deprecate parallelism of Step, pass it to the outer template ([5205bba](https://github.com/deepmodeling/dflow/commit/5205bbaea78350539a0ede98f88ab7caba1a8e58))

## [1.7.70](https://github.com/deepmodeling/dflow/compare/v1.7.69...v1.7.70) (2023-08-25)


### Bug Fixes

* sub_path in debug mode ([234f526](https://github.com/deepmodeling/dflow/commit/234f526458292ced3c785b66bf85c2dd99267c3f))

## [1.7.69](https://github.com/deepmodeling/dflow/compare/v1.7.68...v1.7.69) (2023-08-23)


### Bug Fixes

* support retry a step in a running workflow (experimental) ([f308438](https://github.com/deepmodeling/dflow/commit/f308438bd05c85376b4a944343ef64a5d562ad00))

## [1.7.68](https://github.com/deepmodeling/dflow/compare/v1.7.67...v1.7.68) (2023-08-22)


### Bug Fixes

* add retry policies to python op template ([a61d63e](https://github.com/deepmodeling/dflow/commit/a61d63e5572b5b421e81f578c3d692479f7376df))
* work dir bug caused by process pool executor ([a61d63e](https://github.com/deepmodeling/dflow/commit/a61d63e5572b5b421e81f578c3d692479f7376df))

## [1.7.67](https://github.com/deepmodeling/dflow/compare/v1.7.66...v1.7.67) (2023-08-21)


### Bug Fixes

* optimize deepcopy in debug mode ([a055814](https://github.com/deepmodeling/dflow/commit/a0558140055827ac100c6ca14fa3ac087bc62e7f))

## [1.7.66](https://github.com/deepmodeling/dflow/compare/v1.7.65...v1.7.66) (2023-08-21)


### Bug Fixes

* s3_config['repo'] is str ([cf01616](https://github.com/deepmodeling/dflow/commit/cf016168abb34d2397a6d4002f5812b61bcb30e3))
* s3_config['repo'] is str ([8cf05cb](https://github.com/deepmodeling/dflow/commit/8cf05cbeb621b36bc76ba698b2928bb11dba506c))
* steps.inputs.artifacts[name].source = self.inputs.artifacts[name].source causes large memory usage ([cf01616](https://github.com/deepmodeling/dflow/commit/cf016168abb34d2397a6d4002f5812b61bcb30e3))
* steps.inputs.artifacts[name].source = self.inputs.artifacts[name].source causes large memory usage ([8cf05cb](https://github.com/deepmodeling/dflow/commit/8cf05cbeb621b36bc76ba698b2928bb11dba506c))

## [1.7.65](https://github.com/deepmodeling/dflow/compare/v1.7.64...v1.7.65) (2023-08-17)


### Bug Fixes

* add batch size and batch interval for debug mode ([e066c50](https://github.com/deepmodeling/dflow/commit/e066c50f3ddebab6b74a5c5ce40b9ea9dbc714ac))
* add workaround for unavailable exit code of dispatcher back ([a429b8c](https://github.com/deepmodeling/dflow/commit/a429b8c2546e71582b3a8ec73286ef782baaab87))
* support pool_workers = -1 ([e066c50](https://github.com/deepmodeling/dflow/commit/e066c50f3ddebab6b74a5c5ce40b9ea9dbc714ac))

## [1.7.64](https://github.com/deepmodeling/dflow/compare/v1.7.63...v1.7.64) (2023-08-16)


### Bug Fixes

* output artifact from global outputs in debug mode ([a14f86b](https://github.com/deepmodeling/dflow/commit/a14f86ba7ca345565c3fde2f1862d169256e5cab))

## [1.7.63](https://github.com/deepmodeling/dflow/compare/v1.7.62...v1.7.63) (2023-08-16)


### Bug Fixes

* modify example bohrium dataset ([0bf6ce0](https://github.com/deepmodeling/dflow/commit/0bf6ce094de22c561eef8288a0a3f7894431d65a))

## [1.7.62](https://github.com/deepmodeling/dflow/compare/v1.7.61...v1.7.62) (2023-08-15)


### Bug Fixes

* set local path in record_input_artifacts ([62f67b5](https://github.com/deepmodeling/dflow/commit/62f67b5c9a795cd52438db13caf148af0a448bcc))

## [1.7.61](https://github.com/deepmodeling/dflow/compare/v1.7.60...v1.7.61) (2023-08-15)


### Bug Fixes

* input artifacts of steps ([bf138de](https://github.com/deepmodeling/dflow/commit/bf138dead7ad5cd1d4b6744de6ed394b81d6169b))
* source global output artifacts ([bf138de](https://github.com/deepmodeling/dflow/commit/bf138dead7ad5cd1d4b6744de6ed394b81d6169b))

## [1.7.60](https://github.com/deepmodeling/dflow/compare/v1.7.59...v1.7.60) (2023-08-15)


### Bug Fixes

* dep has no attribute phase ([011f22b](https://github.com/deepmodeling/dflow/commit/011f22bdb0276d9d0e83062d8525b021b33f1b47))

## [1.7.59](https://github.com/deepmodeling/dflow/compare/v1.7.58...v1.7.59) (2023-08-15)


### Bug Fixes

* support depends in debug mode ([f7f50e8](https://github.com/deepmodeling/dflow/commit/f7f50e8d7f9bf10a4236478a5e817f9a2e47eaef))

## [1.7.58](https://github.com/deepmodeling/dflow/compare/v1.7.57...v1.7.58) (2023-08-15)


### Bug Fixes

* subprocess does not inherit envs ([1cb109d](https://github.com/deepmodeling/dflow/commit/1cb109d6163034b4631c38d3ed6190c937410fa4))

## [1.7.57](https://github.com/deepmodeling/dflow/compare/v1.7.56...v1.7.57) (2023-08-14)


### Bug Fixes

* add env to container executor ([bb56a1b](https://github.com/deepmodeling/dflow/commit/bb56a1bc5423a5767ceb08110e069fffd9884637))

## [1.7.56](https://github.com/deepmodeling/dflow/compare/v1.7.55...v1.7.56) (2023-08-14)


### Bug Fixes

* support env var in debug mode ([2a56614](https://github.com/deepmodeling/dflow/commit/2a566140004aa498af434dd5f058d31458f2c979))

## [1.7.55](https://github.com/deepmodeling/dflow/compare/v1.7.54...v1.7.55) (2023-08-11)


### Bug Fixes

* copy singularity instead of symlink ([9187833](https://github.com/deepmodeling/dflow/commit/918783337d720b41e8e2fbeb136a24ffac3db164))
* fix typeguard version ([9187833](https://github.com/deepmodeling/dflow/commit/918783337d720b41e8e2fbeb136a24ffac3db164))

## [1.7.54](https://github.com/deepmodeling/dflow/compare/v1.7.53...v1.7.54) (2023-08-11)


### Bug Fixes

* add container_args to DispatcherExecutor ([582c4e9](https://github.com/deepmodeling/dflow/commit/582c4e9336b39e84761b2170025c42bd080981b4))

## [1.7.53](https://github.com/deepmodeling/dflow/compare/v1.7.52...v1.7.53) (2023-08-11)


### Bug Fixes

* kill jobs on sigterm in dispatcher executor ([01e9a4d](https://github.com/deepmodeling/dflow/commit/01e9a4dcb85a802ce1a1b53a7850f9adb40c73af))
* make dispatcher executor consistent in debug mode and default mode ([01e9a4d](https://github.com/deepmodeling/dflow/commit/01e9a4dcb85a802ce1a1b53a7850f9adb40c73af))
* remove workaround for unavailable exit code of Bohrium job ([01e9a4d](https://github.com/deepmodeling/dflow/commit/01e9a4dcb85a802ce1a1b53a7850f9adb40c73af))
* retry on network error in dispatcher executor ([01e9a4d](https://github.com/deepmodeling/dflow/commit/01e9a4dcb85a802ce1a1b53a7850f9adb40c73af))

## [1.7.52](https://github.com/deepmodeling/dflow/compare/v1.7.51...v1.7.52) (2023-08-10)


### Bug Fixes

* add debug_s3 option ([8f778c8](https://github.com/deepmodeling/dflow/commit/8f778c8ed09f445b048a31d440d4e5b40d5e69eb))
* record script_rendered in yaml ([8f778c8](https://github.com/deepmodeling/dflow/commit/8f778c8ed09f445b048a31d440d4e5b40d5e69eb))

## [1.7.51](https://github.com/deepmodeling/dflow/compare/v1.7.50...v1.7.51) (2023-08-10)


### Bug Fixes

* solve overlap between pathes in upload_artifact ([0042297](https://github.com/deepmodeling/dflow/commit/0042297d1245a1c8e93420140537be61cb59977f))
* support query_global_outputs in debug mode ([0042297](https://github.com/deepmodeling/dflow/commit/0042297d1245a1c8e93420140537be61cb59977f))

## [1.7.50](https://github.com/deepmodeling/dflow/compare/v1.7.49...v1.7.50) (2023-08-09)


### Bug Fixes

* set private_key_host_path to None by default ([af8a612](https://github.com/deepmodeling/dflow/commit/af8a612921fd0eed4cff2ccb53a9aeb869d78099))

## [1.7.49](https://github.com/deepmodeling/dflow/compare/v1.7.48...v1.7.49) (2023-08-09)


### Bug Fixes

* support wf.to_yaml() in debug mode ([3e2954f](https://github.com/deepmodeling/dflow/commit/3e2954f9bc03152ded849a9fbe9343b3bc0e0030))

## [1.7.48](https://github.com/deepmodeling/dflow/compare/v1.7.47...v1.7.48) (2023-08-09)


### Bug Fixes

* add_slices of PythonOPTemplate ([d1a73d0](https://github.com/deepmodeling/dflow/commit/d1a73d0baf842a3cfb26546a799b7c9b7ebdcd31))

## [1.7.47](https://github.com/deepmodeling/dflow/compare/v1.7.46...v1.7.47) (2023-08-09)


### Bug Fixes

* _from -&gt; raw when submit from yaml to argo ([f970e44](https://github.com/deepmodeling/dflow/commit/f970e4442295c15be5cd1ad54a78d5781ade55ec))
* do not reuse keys in global outputs when save_keys_in_global_outputs=False ([1ffdad3](https://github.com/deepmodeling/dflow/commit/1ffdad3343e08c8b72d27b31df55b5b5bcb46f1e))

## [1.7.46](https://github.com/deepmodeling/dflow/compare/v1.7.45...v1.7.46) (2023-08-08)


### Bug Fixes

* add labels, node_selector to OP template ([d8f35dc](https://github.com/deepmodeling/dflow/commit/d8f35dcd2fb523c66589cfb4e16902cc8906e40e))

## [1.7.45](https://github.com/deepmodeling/dflow/compare/v1.7.44...v1.7.45) (2023-08-08)


### Bug Fixes

* add cpu and memory to container executor ([101fb96](https://github.com/deepmodeling/dflow/commit/101fb96d3bebe1ba994b10a5a23702b6017c337c))

## [1.7.44](https://github.com/deepmodeling/dflow/compare/v1.7.43...v1.7.44) (2023-08-04)


### Bug Fixes

* support input/output path not begining with /tmp in container executor ([de2b36b](https://github.com/deepmodeling/dflow/commit/de2b36bcca5a9d46768e75617f8ff4b9a3a551fb))
* support volume mounts for container executor ([f00c18b](https://github.com/deepmodeling/dflow/commit/f00c18bb4aede54d63ff6a368dbb51077a7fa198))

## [1.7.43](https://github.com/deepmodeling/dflow/compare/v1.7.42...v1.7.43) (2023-08-04)


### Bug Fixes

* support local path in dflow yaml ([ba32a39](https://github.com/deepmodeling/dflow/commit/ba32a395751ae8e7cf7ace97ec6cc9e256bfd961))

## [1.7.42](https://github.com/deepmodeling/dflow/compare/v1.7.41...v1.7.42) (2023-08-03)


### Bug Fixes

* multi-merge ([6eb661d](https://github.com/deepmodeling/dflow/commit/6eb661d7460fe3820ffe8e2d5e7dfa431f22f605))

## [1.7.41](https://github.com/deepmodeling/dflow/compare/v1.7.40...v1.7.41) (2023-08-02)


### Bug Fixes

* interactive bash causes process suspended ([41999a2](https://github.com/deepmodeling/dflow/commit/41999a220a1039398d35799852dfe0f441ca8b8b))

## [1.7.40](https://github.com/deepmodeling/dflow/compare/v1.7.39...v1.7.40) (2023-07-29)


### Bug Fixes

* InputParameter/OutputParameter has no attribute is_str ([65c3782](https://github.com/deepmodeling/dflow/commit/65c3782ee7ef4e03418c473dcf056fdf129564a3))

## [1.7.39](https://github.com/deepmodeling/dflow/compare/v1.7.38...v1.7.39) (2023-07-29)


### Bug Fixes

* convert item of ArgoVar correctly ([0f51882](https://github.com/deepmodeling/dflow/commit/0f518825ed775f2c3bae22784182cab4717f9b1e))

## [1.7.38](https://github.com/deepmodeling/dflow/compare/v1.7.37...v1.7.38) (2023-07-28)


### Bug Fixes

* avoid exponentially increase of memory ([000e40c](https://github.com/deepmodeling/dflow/commit/000e40c1aab641c1d97f3ffc4a9287415daef020))

## [1.7.37](https://github.com/deepmodeling/dflow/compare/v1.7.36...v1.7.37) (2023-07-28)


### Bug Fixes

* add support for datasets+models ([ff90d6c](https://github.com/deepmodeling/dflow/commit/ff90d6cdcfba4e7b436db115e484c40cc864a941))
* cannot pickle &lt;local&gt;.Artifact ([ff90d6c](https://github.com/deepmodeling/dflow/commit/ff90d6cdcfba4e7b436db115e484c40cc864a941))
* cross link ([ff90d6c](https://github.com/deepmodeling/dflow/commit/ff90d6cdcfba4e7b436db115e484c40cc864a941))
* logging.warning ([ff90d6c](https://github.com/deepmodeling/dflow/commit/ff90d6cdcfba4e7b436db115e484c40cc864a941))

## [1.7.36](https://github.com/deepmodeling/dflow/compare/v1.7.35...v1.7.36) (2023-07-27)


### Bug Fixes

* prepare inputs again in restarting if the step failed at pending ([6705d90](https://github.com/deepmodeling/dflow/commit/6705d904feb52c87316bba85af408a397fec9117))
* retrieve exception of subprocess when pool.submit fails ([6705d90](https://github.com/deepmodeling/dflow/commit/6705d904feb52c87316bba85af408a397fec9117))

## [1.7.35](https://github.com/deepmodeling/dflow/compare/v1.7.34...v1.7.35) (2023-07-26)


### Bug Fixes

* dispatcher executor modified after render ([08d545d](https://github.com/deepmodeling/dflow/commit/08d545d92edca18c9242b08aad60db0f2d23617d))

## [1.7.34](https://github.com/deepmodeling/dflow/compare/v1.7.33...v1.7.34) (2023-07-21)


### Bug Fixes

* add error message when lbg not installed ([9c41e12](https://github.com/deepmodeling/dflow/commit/9c41e125c951328d4c75f5d69a4768829704f62b))
* enhance restart mechanism in debug mode ([9c41e12](https://github.com/deepmodeling/dflow/commit/9c41e125c951328d4c75f5d69a4768829704f62b))

## [1.7.33](https://github.com/deepmodeling/dflow/compare/v1.7.32...v1.7.33) (2023-07-20)


### Bug Fixes

* add art_root attribute to input artifact ([225a664](https://github.com/deepmodeling/dflow/commit/225a664b869e9a26811cef9b77ac9d2988d15c02))
* add syntax sugar for super OP ([d33f2f7](https://github.com/deepmodeling/dflow/commit/d33f2f75d11dc0b819e97527287a54df4657e3d9))
* set object attribute instead of class attribute ([a94f8e8](https://github.com/deepmodeling/dflow/commit/a94f8e8730a06c17af4bcf70419db7d4326ca1ba))
* support for tuple and single type for OP returns ([d33f2f7](https://github.com/deepmodeling/dflow/commit/d33f2f75d11dc0b819e97527287a54df4657e3d9))

## [1.7.32](https://github.com/deepmodeling/dflow/compare/v1.7.31...v1.7.32) (2023-07-19)


### Bug Fixes

* merge with_param from sub-path slices of artifact list with original argo_enumerate ([11b5b5d](https://github.com/deepmodeling/dflow/commit/11b5b5d411275d47184a1474b0745e907f55f280))

## [1.7.31](https://github.com/deepmodeling/dflow/compare/v1.7.30...v1.7.31) (2023-07-19)


### Bug Fixes

* 'list' object has no attribute 'source' ([b59d5b6](https://github.com/deepmodeling/dflow/commit/b59d5b6dd9eea01e9e884b220743ed4da32c6ee8))

## [1.7.30](https://github.com/deepmodeling/dflow/compare/v1.7.29...v1.7.30) (2023-07-17)


### Bug Fixes

* convert Path/ArgoVar to str ([c64f230](https://github.com/deepmodeling/dflow/commit/c64f230891a6a13dfd7acb7c98b745e9f3b4783a))
* make secret reusable ([c64f230](https://github.com/deepmodeling/dflow/commit/c64f230891a6a13dfd7acb7c98b745e9f3b4783a))

## [1.7.29](https://github.com/deepmodeling/dflow/compare/v1.7.28...v1.7.29) (2023-07-14)


### Bug Fixes

* concat ArgoVar to str ([c84efb6](https://github.com/deepmodeling/dflow/commit/c84efb6813915fada014de2d99f9503169f2ac54))
* support for sub_path syntax in steps/dag context for custom artifacts ([f84fb09](https://github.com/deepmodeling/dflow/commit/f84fb09c02cb66569a064277cb6d4476cc1e37a5))
* support for task kwargs in syntax sugar ([f84fb09](https://github.com/deepmodeling/dflow/commit/f84fb09c02cb66569a064277cb6d4476cc1e37a5))
* use urn to record custom artifacts instead of jsonpickle ([f84fb09](https://github.com/deepmodeling/dflow/commit/f84fb09c02cb66569a064277cb6d4476cc1e37a5))

## [1.7.28](https://github.com/deepmodeling/dflow/compare/v1.7.27...v1.7.28) (2023-07-13)


### Bug Fixes

* nested slices of steps ([b7df96b](https://github.com/deepmodeling/dflow/commit/b7df96b84f5a7eca479e337255f577359dbcfea0))

## [1.7.27](https://github.com/deepmodeling/dflow/compare/v1.7.26...v1.7.27) (2023-07-12)


### Bug Fixes

* syntax sugar for python op template and task ([5521eef](https://github.com/deepmodeling/dflow/commit/5521eefdcf99050f8cf918d39411d7c3ccb13e33))

## [1.7.26](https://github.com/deepmodeling/dflow/compare/v1.7.25...v1.7.26) (2023-07-12)


### Bug Fixes

* sub-path slices of artifact list ([955db41](https://github.com/deepmodeling/dflow/commit/955db418f9c5eccf984be8ee87d4257415b37143))

## [1.7.25](https://github.com/deepmodeling/dflow/compare/v1.7.24...v1.7.25) (2023-07-11)


### Bug Fixes

* merge path list and path dict to path object ([56efbde](https://github.com/deepmodeling/dflow/commit/56efbde8791da879267824136d73a337d35db1aa))

## [1.7.24](https://github.com/deepmodeling/dflow/compare/v1.7.23...v1.7.24) (2023-07-11)


### Bug Fixes

* support for sub_path of datasets artifact ([56b6444](https://github.com/deepmodeling/dflow/commit/56b64448b96e5b6f3d22ced459036a4b7b0a6b00))
* version of sub_path of datasets artifact ([e14d663](https://github.com/deepmodeling/dflow/commit/e14d663b146790cfb110045aef04b14e838f709e))

## [1.7.23](https://github.com/deepmodeling/dflow/compare/v1.7.22...v1.7.23) (2023-07-10)


### Bug Fixes

* support for bohrium ticket ([eba6998](https://github.com/deepmodeling/dflow/commit/eba69986b6102eaefc3e5c01f429799b44bca8d4))
* support for list of lists of path and list of duplicated path ([eba6998](https://github.com/deepmodeling/dflow/commit/eba69986b6102eaefc3e5c01f429799b44bca8d4))

## [1.7.22](https://github.com/deepmodeling/dflow/compare/v1.7.21...v1.7.22) (2023-07-07)


### Bug Fixes

* add python packages to env PYTHONPATH ([e5977a2](https://github.com/deepmodeling/dflow/commit/e5977a265de07855e82bca27d383a90f1e4b1a9c))

## [1.7.21](https://github.com/deepmodeling/dflow/compare/v1.7.20...v1.7.21) (2023-07-07)


### Bug Fixes

* pass list of datasets artifacts to steps ([8e4cd62](https://github.com/deepmodeling/dflow/commit/8e4cd62e737a0d7192bb54e18ce388c122c8fa4a))

## [1.7.20](https://github.com/deepmodeling/dflow/compare/v1.7.19...v1.7.20) (2023-07-07)


### Bug Fixes

* copy on write ([a2c9a0e](https://github.com/deepmodeling/dflow/commit/a2c9a0ed20ca70b90fd539871225200ec3c4884c))
* support for list of datasets artifacts ([a2c9a0e](https://github.com/deepmodeling/dflow/commit/a2c9a0ed20ca70b90fd539871225200ec3c4884c))

## [1.7.19](https://github.com/deepmodeling/dflow/compare/v1.7.18...v1.7.19) (2023-07-07)


### Bug Fixes

* download artifact with specified copy method ([09fe23a](https://github.com/deepmodeling/dflow/commit/09fe23aa87e04eea63dd7f8a4498f5e368139d36))

## [1.7.18](https://github.com/deepmodeling/dflow/compare/v1.7.17...v1.7.18) (2023-07-07)


### Bug Fixes

* query step by name in debug mode ([1b90b67](https://github.com/deepmodeling/dflow/commit/1b90b67a35a4d6dc09c49579eb5276372cff7f0a))

## [1.7.17](https://github.com/deepmodeling/dflow/compare/v1.7.16...v1.7.17) (2023-07-06)


### Bug Fixes

* try link except copy ([a7b4f46](https://github.com/deepmodeling/dflow/commit/a7b4f4608eee7bccb54c93ba110b6f54640d91e6))

## [1.7.16](https://github.com/deepmodeling/dflow/compare/v1.7.15...v1.7.16) (2023-07-06)


### Bug Fixes

* cross-device link ([0edf41a](https://github.com/deepmodeling/dflow/commit/0edf41a81bdfb0283d12925811728bd9248e5465))

## [1.7.15](https://github.com/deepmodeling/dflow/compare/v1.7.14...v1.7.15) (2023-07-06)


### Bug Fixes

* . not allowed in key ([6063ddd](https://github.com/deepmodeling/dflow/commit/6063dddcb26aa2ded667702c564aef093213f2a1))
* avoid recursive symlink; ([6063ddd](https://github.com/deepmodeling/dflow/commit/6063dddcb26aa2ded667702c564aef093213f2a1))

## [1.7.14](https://github.com/deepmodeling/dflow/compare/v1.7.13...v1.7.14) (2023-07-04)


### Bug Fixes

* add detect_empty_dir to config ([4504cad](https://github.com/deepmodeling/dflow/commit/4504cad7a8868a506a4459007c18322e0dfffbd3))

## [1.7.13](https://github.com/deepmodeling/dflow/compare/v1.7.12...v1.7.13) (2023-07-04)


### Bug Fixes

* make template reusable when use datasets artifact ([6405062](https://github.com/deepmodeling/dflow/commit/6405062afc41764d84bd5765e8e7b246da9a201f))
* terminate in debug mode ([6405062](https://github.com/deepmodeling/dflow/commit/6405062afc41764d84bd5765e8e7b246da9a201f))

## [1.7.12](https://github.com/deepmodeling/dflow/compare/v1.7.11...v1.7.12) (2023-07-02)


### Bug Fixes

* deduplicate argo templates ([23f88bf](https://github.com/deepmodeling/dflow/commit/23f88bf094b856e86546fa67f0eb8caa51916312))
* shallow copy super op ([23f88bf](https://github.com/deepmodeling/dflow/commit/23f88bf094b856e86546fa67f0eb8caa51916312))

## [1.7.11](https://github.com/deepmodeling/dflow/compare/v1.7.10...v1.7.11) (2023-06-30)


### Bug Fixes

* use ProcessPoolExecutor instead of Process in debug mode ([a692bad](https://github.com/deepmodeling/dflow/commit/a692bad23ffc2d043aad0ac8ac9aa8f93497525b))
* validate workflow/template/parameter/artifact/key name ([a692bad](https://github.com/deepmodeling/dflow/commit/a692bad23ffc2d043aad0ac8ac9aa8f93497525b))

## [1.7.10](https://github.com/deepmodeling/dflow/compare/v1.7.9...v1.7.10) (2023-06-29)


### Bug Fixes

* support for steps + slices + list of artifact ([49b0318](https://github.com/deepmodeling/dflow/commit/49b0318a5e3343d2939422050d0d28a27c25e8bf))

## [1.7.9](https://github.com/deepmodeling/dflow/compare/v1.7.8...v1.7.9) (2023-06-29)


### Bug Fixes

* add auto loop ([68c5d84](https://github.com/deepmodeling/dflow/commit/68c5d84adea808f4229c83664755b1c22d25f972))
* bug in add slices to python op template ([68c5d84](https://github.com/deepmodeling/dflow/commit/68c5d84adea808f4229c83664755b1c22d25f972))

## [1.7.8](https://github.com/deepmodeling/dflow/compare/v1.7.7...v1.7.8) (2023-06-29)


### Bug Fixes

* make a random directory when output artifact path equals to input artifact path ([ce8cb7d](https://github.com/deepmodeling/dflow/commit/ce8cb7da807b2701af868e96c478c69d2faa07b1))

## [1.7.7](https://github.com/deepmodeling/dflow/compare/v1.7.6...v1.7.7) (2023-06-28)


### Bug Fixes

* take apart input_artifact_prefix from input_artifact_slices ([d5eaac0](https://github.com/deepmodeling/dflow/commit/d5eaac06f97d1234f09b37a10fe8e44a74b05d9c))

## [1.7.6](https://github.com/deepmodeling/dflow/compare/v1.7.5...v1.7.6) (2023-06-27)


### Bug Fixes

* support for multi arguments to argo_enumerate ([c58e9ea](https://github.com/deepmodeling/dflow/commit/c58e9ea9eb95839a8167b066bbe23e3b52177546))

## [1.7.5](https://github.com/deepmodeling/dflow/compare/v1.7.4...v1.7.5) (2023-06-19)


### Bug Fixes

* skip unmerged output artifact of reused sliced steps ([c516396](https://github.com/deepmodeling/dflow/commit/c5163969c4fe07faef12677ac29086792a11a4d8))
* support link and copy for copy method in debug mode ([c516396](https://github.com/deepmodeling/dflow/commit/c5163969c4fe07faef12677ac29086792a11a4d8))

## [1.7.4](https://github.com/deepmodeling/dflow/compare/v1.7.3...v1.7.4) (2023-06-14)


### Bug Fixes

* follow_symlinks=True of os.link not work on Linux ([4779672](https://github.com/deepmodeling/dflow/commit/4779672d08413cc45b2076b0e46864e3e8aa1dae))

## [1.7.3](https://github.com/deepmodeling/dflow/compare/v1.7.2...v1.7.3) (2023-06-13)


### Bug Fixes

* name in input signs not in input artifacts after set list/dict of artifacts ([71cabf9](https://github.com/deepmodeling/dflow/commit/71cabf914f25c5ecab4d3b3e01f8f9a90d40390b))
* raise error when download failed in debug mode ([71cabf9](https://github.com/deepmodeling/dflow/commit/71cabf914f25c5ecab4d3b3e01f8f9a90d40390b))

## [1.7.2](https://github.com/deepmodeling/dflow/compare/v1.7.1...v1.7.2) (2023-06-13)


### Bug Fixes

* par has no attr value ([8fa769e](https://github.com/deepmodeling/dflow/commit/8fa769e323e729c794e9cd0b13110a8e6eed25db))

## [1.7.1](https://github.com/deepmodeling/dflow/compare/v1.7.0...v1.7.1) (2023-06-12)


### Bug Fixes

* parallel steps has no attribute inputs ([04093b0](https://github.com/deepmodeling/dflow/commit/04093b08811cc97ec63faf2e71436cd2ea503c42))

## [1.7.0](https://github.com/deepmodeling/dflow/compare/v1.6.148...v1.7.0) (2023-06-12)


### Features

* support for slicing nested steps/dagreplace the method of set slices of PythonOPTemplate with set_slices ([f149c99](https://github.com/deepmodeling/dflow/commit/f149c991ba33474a047f3d58c662818c64449eed))

## [1.6.148](https://github.com/deepmodeling/dflow/compare/v1.6.147...v1.6.148) (2023-06-12)


### Bug Fixes

* add clean option to dispatcher executor ([c7a8431](https://github.com/deepmodeling/dflow/commit/c7a84313c8b3d37301e8bfdcea813ee6f44be118))

## [1.6.147](https://github.com/deepmodeling/dflow/compare/v1.6.146...v1.6.147) (2023-06-12)


### Bug Fixes

* inspect.getsourcefile returns relative path in python&lt;=3.8 ([ac4f72e](https://github.com/deepmodeling/dflow/commit/ac4f72ed509d91577044e029f7a4eddbe3b23fd9))

## [1.6.146](https://github.com/deepmodeling/dflow/compare/v1.6.145...v1.6.146) (2023-06-11)


### Bug Fixes

* add VERSION to MANIFEST.in ([e489461](https://github.com/deepmodeling/dflow/commit/e48946102c5f25f281be236f11087338be0f55f8))

## [1.6.145](https://github.com/deepmodeling/dflow/compare/v1.6.144...v1.6.145) (2023-06-10)


### Bug Fixes

* add VERSION to package data ([d2c9883](https://github.com/deepmodeling/dflow/commit/d2c9883b2de982c57d8f8bcf93ee2c74f919d8e0))

## [1.6.144](https://github.com/deepmodeling/dflow/compare/v1.6.143...v1.6.144) (2023-06-10)


### Bug Fixes

* add VERSION to package data ([6b56a3c](https://github.com/deepmodeling/dflow/commit/6b56a3c6040ba695f4a594e990ec4434b64a9b66))

## [1.6.143](https://github.com/deepmodeling/dflow/compare/v1.6.142...v1.6.143) (2023-06-09)


### Bug Fixes

* get log level from env var ([bc5221d](https://github.com/deepmodeling/dflow/commit/bc5221d62298afe3894ee249e305855e8241af72))
* log info when failed to get source code ([bc5221d](https://github.com/deepmodeling/dflow/commit/bc5221d62298afe3894ee249e305855e8241af72))

## [1.6.142](https://github.com/deepmodeling/dflow/compare/v1.6.141...v1.6.142) (2023-06-08)


### Bug Fixes

* support datasets in container/remote context ([6b47487](https://github.com/deepmodeling/dflow/commit/6b47487253f2c11c5266035d6baa5a17f8fc09c9))

## [1.6.141](https://github.com/deepmodeling/dflow/compare/v1.6.140...v1.6.141) (2023-06-07)


### Bug Fixes

* add datasets plugin ([b9ee6e7](https://github.com/deepmodeling/dflow/commit/b9ee6e73fe4e99e3d4076a045bdabc3e4773c711))

## [1.6.140](https://github.com/deepmodeling/dflow/compare/v1.6.139...v1.6.140) (2023-05-30)


### Bug Fixes

* update slurm tutorial with dispatcher executor ([1398d9f](https://github.com/deepmodeling/dflow/commit/1398d9ff979aeb00c7e4751df12ef8fc2e2ededa))

## [1.6.139](https://github.com/deepmodeling/dflow/compare/v1.6.138...v1.6.139) (2023-05-29)


### Bug Fixes

* depends on success of task by default in dag ([14ec71a](https://github.com/deepmodeling/dflow/commit/14ec71a4119678fe5824c0fa785b253499118d19))

## [1.6.138](https://github.com/deepmodeling/dflow/compare/v1.6.137...v1.6.138) (2023-05-29)


### Bug Fixes

* incompatibility across python version of cloudpickle in tutorials ([94e0ad5](https://github.com/deepmodeling/dflow/commit/94e0ad5b5cda6a5f0e207a6afd0093c5ad55b9a2))
* replace dependencies with depends in dag ([5f08042](https://github.com/deepmodeling/dflow/commit/5f0804242dc697b88628674e6e8044edfb00e3d0))

## [1.6.137](https://github.com/deepmodeling/dflow/compare/v1.6.136...v1.6.137) (2023-05-29)


### Bug Fixes

* add argo_enumerate ([2ae1a7d](https://github.com/deepmodeling/dflow/commit/2ae1a7dcea838318ea5c9d72dc4459c22903143d))

## [1.6.136](https://github.com/deepmodeling/dflow/compare/v1.6.135...v1.6.136) (2023-05-29)


### Bug Fixes

* a bug in ArgoVar plus string ([26a9910](https://github.com/deepmodeling/dflow/commit/26a991076aaaa68dbd09fd0ee30e62d58f6f9fdd))

## [1.6.135](https://github.com/deepmodeling/dflow/compare/v1.6.134...v1.6.135) (2023-05-29)


### Bug Fixes

* support ArgoVar add string ([ddd6234](https://github.com/deepmodeling/dflow/commit/ddd62341795eefd21fbef4d66222aeaba6bdf352))
* support call sub_path of InputArtifact/OutputArtifact multi times ([ddd6234](https://github.com/deepmodeling/dflow/commit/ddd62341795eefd21fbef4d66222aeaba6bdf352))
* support pass ArgoVar to sub_path method of InputArtifact/OutputArtifact ([ddd6234](https://github.com/deepmodeling/dflow/commit/ddd62341795eefd21fbef4d66222aeaba6bdf352))

## [1.6.134](https://github.com/deepmodeling/dflow/compare/v1.6.133...v1.6.134) (2023-05-25)


### Bug Fixes

* do not parse repo when repo is provided ([ac8bb40](https://github.com/deepmodeling/dflow/commit/ac8bb40629a98977ee72fddf539fdbabe1512a7a))
* parse repo when import dflow if repo_key is provided ([ac8bb40](https://github.com/deepmodeling/dflow/commit/ac8bb40629a98977ee72fddf539fdbabe1512a7a))

## [1.6.133](https://github.com/deepmodeling/dflow/compare/v1.6.132...v1.6.133) (2023-05-24)


### Bug Fixes

* use OSS client to upload ([b05c373](https://github.com/deepmodeling/dflow/commit/b05c3730bdf8f59b610f1c43b5d99404185acc99))

## [1.6.132](https://github.com/deepmodeling/dflow/compare/v1.6.131...v1.6.132) (2023-05-23)


### Bug Fixes

* property name and method name of input artifact conflict ([a0aa612](https://github.com/deepmodeling/dflow/commit/a0aa612c06e20b73f013e72d907265f9a433e590))

## [1.6.131](https://github.com/deepmodeling/dflow/compare/v1.6.130...v1.6.131) (2023-05-22)


### Bug Fixes

* remove cleaning output path in debug mode ([279c22e](https://github.com/deepmodeling/dflow/commit/279c22e4858f50f5444ed1ef72f123789128e809))
* render item in artifact key in debug mode ([279c22e](https://github.com/deepmodeling/dflow/commit/279c22e4858f50f5444ed1ef72f123789128e809))
* repeatedly try to make symbolic link for global output artifact in debug mode ([279c22e](https://github.com/deepmodeling/dflow/commit/279c22e4858f50f5444ed1ef72f123789128e809))
* syntax error [[ of sh ([279c22e](https://github.com/deepmodeling/dflow/commit/279c22e4858f50f5444ed1ef72f123789128e809))

## [1.6.130](https://github.com/deepmodeling/dflow/compare/v1.6.129...v1.6.130) (2023-05-20)


### Bug Fixes

* add detach mode for running workflows locally ([0b06961](https://github.com/deepmodeling/dflow/commit/0b06961a8a859f88061fe68e95dca6b6dd5aab6b))

## [1.6.129](https://github.com/deepmodeling/dflow/compare/v1.6.128...v1.6.129) (2023-05-18)


### Bug Fixes

* add tqdm to download_s3 ([e6a6cbf](https://github.com/deepmodeling/dflow/commit/e6a6cbf418ecc5b441c7b91411749cf5c8fab525))
* write phase file when step fails in debug mode ([e6a6cbf](https://github.com/deepmodeling/dflow/commit/e6a6cbf418ecc5b441c7b91411749cf5c8fab525))

## [1.6.128](https://github.com/deepmodeling/dflow/compare/v1.6.127...v1.6.128) (2023-05-17)


### Bug Fixes

* change type hint ABCMeta -&gt; Type[OP] ([1f654c6](https://github.com/deepmodeling/dflow/commit/1f654c64f517b7b0ac6853267ee13421c4eb2e93))
* export ArgoStep and ArgoWorkflow ([1f654c6](https://github.com/deepmodeling/dflow/commit/1f654c64f517b7b0ac6853267ee13421c4eb2e93))

## [1.6.127](https://github.com/deepmodeling/dflow/compare/v1.6.126...v1.6.127) (2023-05-17)


### Bug Fixes

* pyright issues ([967278d](https://github.com/deepmodeling/dflow/commit/967278d9f4889a59bc1269baad5790c3b23f6b61))

## [1.6.126](https://github.com/deepmodeling/dflow/compare/v1.6.125...v1.6.126) (2023-05-14)


### Bug Fixes

* add pre_script and post_script to dispatcher executor ([bba57ff](https://github.com/deepmodeling/dflow/commit/bba57ff8204db46e16dea79a9e5796b13680380b))

## [1.6.125](https://github.com/deepmodeling/dflow/compare/v1.6.124...v1.6.125) (2023-05-12)


### Bug Fixes

* add shuffle to slices group ([7cb23f0](https://github.com/deepmodeling/dflow/commit/7cb23f0e2e60e8cb4228d2a278b74c9e7b340a12))

## [1.6.124](https://github.com/deepmodeling/dflow/compare/v1.6.123...v1.6.124) (2023-05-12)


### Bug Fixes

* undefined wfdir in debug mode ([875f1e4](https://github.com/deepmodeling/dflow/commit/875f1e4012ff0d3f7b1ccf763636354ec0f2d522))

## [1.6.123](https://github.com/deepmodeling/dflow/compare/v1.6.122...v1.6.123) (2023-05-05)


### Bug Fixes

* add __sub__, __mul__ and __truediv__ methods to ArgoVar ([469ef6d](https://github.com/deepmodeling/dflow/commit/469ef6d4be59a57c175c86c1e9c894cd9059cd8a))
* prepend workflow id to step id in debug mode ([469ef6d](https://github.com/deepmodeling/dflow/commit/469ef6d4be59a57c175c86c1e9c894cd9059cd8a))

## [1.6.122](https://github.com/deepmodeling/dflow/compare/v1.6.121...v1.6.122) (2023-05-05)


### Bug Fixes

* raise error on missing module when jsonpickle.loads ([aec5bbe](https://github.com/deepmodeling/dflow/commit/aec5bbe350fedcad470f2909613cce2bc2670413))

## [1.6.121](https://github.com/deepmodeling/dflow/compare/v1.6.120...v1.6.121) (2023-05-04)


### Bug Fixes

* handle str when passing dict of parameters ([e45b40a](https://github.com/deepmodeling/dflow/commit/e45b40af0a56d375f7d53de8f380fac2e1754ef7))

## [1.6.120](https://github.com/deepmodeling/dflow/compare/v1.6.119...v1.6.120) (2023-05-04)


### Bug Fixes

* move V1alpha1RetryStrategy to convert_to_argo method ([8f764a9](https://github.com/deepmodeling/dflow/commit/8f764a91615bbca27daa9359d997750a226edd25))

## [1.6.119](https://github.com/deepmodeling/dflow/compare/v1.6.118...v1.6.119) (2023-04-26)


### Bug Fixes

* support for submitting workflow with ID ([4bd2f84](https://github.com/deepmodeling/dflow/commit/4bd2f84f953eadf2e80ce64a8364ea8a53241e93))

## [1.6.118](https://github.com/deepmodeling/dflow/compare/v1.6.117...v1.6.118) (2023-04-26)


### Bug Fixes

* optimize group_size when with_param is argo_range ([068dd53](https://github.com/deepmodeling/dflow/commit/068dd53514dfc9e16d6a0983198c04230a9f92c3))

## [1.6.117](https://github.com/deepmodeling/dflow/compare/v1.6.116...v1.6.117) (2023-04-24)


### Bug Fixes

* support for using local singularity image ([ebf9595](https://github.com/deepmodeling/dflow/commit/ebf959567aeec26fe12e46e627a269142f030b7f))

## [1.6.116](https://github.com/deepmodeling/dflow/compare/v1.6.115...v1.6.116) (2023-04-23)


### Bug Fixes

* handle dependencies of task for passing a dict of parameters/artifacts ([4be10d8](https://github.com/deepmodeling/dflow/commit/4be10d8b21732600f6e5f92e59fe3c99b7cd5f49))

## [1.6.115](https://github.com/deepmodeling/dflow/compare/v1.6.114...v1.6.115) (2023-04-23)


### Bug Fixes

* support for passing a dict or list containing ArgoVar ([be5fe8d](https://github.com/deepmodeling/dflow/commit/be5fe8dc5eea3a32a34dd2a15d1905b1b97af856))

## [1.6.114](https://github.com/deepmodeling/dflow/compare/v1.6.113...v1.6.114) (2023-04-22)


### Bug Fixes

* a bug in dict argument of artifacts ([4447fe5](https://github.com/deepmodeling/dflow/commit/4447fe5d17eb4632b75e0ee1e5400a5109551e28))

## [1.6.113](https://github.com/deepmodeling/dflow/compare/v1.6.112...v1.6.113) (2023-04-22)


### Bug Fixes

* support for pass a dict of artifacts as argument for a step ([9431af0](https://github.com/deepmodeling/dflow/commit/9431af0765311676c3d1c717e52f680666a14700))

## [1.6.112](https://github.com/deepmodeling/dflow/compare/v1.6.111...v1.6.112) (2023-04-19)


### Bug Fixes

* close stdin after write input in run_command ([f6b651f](https://github.com/deepmodeling/dflow/commit/f6b651fce5abeac8eaf4f6ee1bcb532ea9696289))

## [1.6.111](https://github.com/deepmodeling/dflow/compare/v1.6.110...v1.6.111) (2023-04-19)


### Bug Fixes

* set PYTHONUNBUFFERED=true to output real-time log in dispatcher executor ([d912e0d](https://github.com/deepmodeling/dflow/commit/d912e0d6212a4e064d86c19b43f38a5974040812))

## [1.6.110](https://github.com/deepmodeling/dflow/compare/v1.6.109...v1.6.110) (2023-04-18)


### Bug Fixes

* triple quotes in user's script ([b9114a7](https://github.com/deepmodeling/dflow/commit/b9114a7b1e02ba81458ce24625f800a6453830dd))

## [1.6.109](https://github.com/deepmodeling/dflow/compare/v1.6.108...v1.6.109) (2023-04-17)


### Bug Fixes

* support for HTTP artifact ([cf772eb](https://github.com/deepmodeling/dflow/commit/cf772eb4482100a5d54553f42a0fa3e5f08cedeb))

## [1.6.108](https://github.com/deepmodeling/dflow/compare/v1.6.107...v1.6.108) (2023-04-17)


### Bug Fixes

* escaping in dispatcher executor ([5cd833a](https://github.com/deepmodeling/dflow/commit/5cd833aefbc3824b1e35eac7b3c5806961039c31))

## [1.6.107](https://github.com/deepmodeling/dflow/compare/v1.6.106...v1.6.107) (2023-04-13)


### Bug Fixes

* add container executor ([0f7f275](https://github.com/deepmodeling/dflow/commit/0f7f27512e60da12b01dab98e608ae068d94978f))
* add container_engine annotation ([0f7f275](https://github.com/deepmodeling/dflow/commit/0f7f27512e60da12b01dab98e608ae068d94978f))

## [1.6.106](https://github.com/deepmodeling/dflow/compare/v1.6.105...v1.6.106) (2023-04-13)


### Bug Fixes

* subpath slices for optional artifact ([123ecb8](https://github.com/deepmodeling/dflow/commit/123ecb8b47634b532945ea527df7353000362451))

## [1.6.105](https://github.com/deepmodeling/dflow/compare/v1.6.104...v1.6.105) (2023-04-07)


### Bug Fixes

* make tutorials compatible for argo 3.4.1 ([a207ec4](https://github.com/deepmodeling/dflow/commit/a207ec47e3f2e782485fe34d07c28ce6f00ce6fb))
* update readme ([289f96b](https://github.com/deepmodeling/dflow/commit/289f96bac5705e193cc130257ff6c060a07390de))

## [1.6.104](https://github.com/deepmodeling/dflow/compare/v1.6.103...v1.6.104) (2023-04-05)


### Bug Fixes

* remove duplicated path in init-artifact of sub-path mode ([3a6591a](https://github.com/deepmodeling/dflow/commit/3a6591abf8cbc5083b8cbe5b8d80a81031cd0de8))

## [1.6.103](https://github.com/deepmodeling/dflow/compare/v1.6.102...v1.6.103) (2023-04-05)


### Bug Fixes

* sub_path argument of download_artifact ([cc447d3](https://github.com/deepmodeling/dflow/commit/cc447d33ae77b3a73009d557a82993aeaedd5444))

## [1.6.102](https://github.com/deepmodeling/dflow/compare/v1.6.101...v1.6.102) (2023-04-03)


### Bug Fixes

* convert OP template to launching parser ([895a938](https://github.com/deepmodeling/dflow/commit/895a93895826fa3833a637a1edac67d6c29227f6))

## [1.6.101](https://github.com/deepmodeling/dflow/compare/v1.6.100...v1.6.101) (2023-04-03)


### Bug Fixes

* convert OP to launching parser ([571acf7](https://github.com/deepmodeling/dflow/commit/571acf7dbb1b28e62869819671dec416bd592a74))

## [1.6.100](https://github.com/deepmodeling/dflow/compare/v1.6.99...v1.6.100) (2023-03-29)


### Bug Fixes

* reusing sliced steps in sub-path mode ([49c178d](https://github.com/deepmodeling/dflow/commit/49c178d2d32ece247b3d5edac6ab41a3dcd4319b))

## [1.6.99](https://github.com/deepmodeling/dflow/compare/v1.6.98...v1.6.99) (2023-03-28)


### Bug Fixes

* inconsistent behaviors between oss and s3 ([f7403f2](https://github.com/deepmodeling/dflow/commit/f7403f2ae1572e87be5cffc1d989ad0b1ca5d909))
* path returned by download_artifact when slice is provided ([58449a7](https://github.com/deepmodeling/dflow/commit/58449a735c767b6d436d72f95742b4d5a08d5aa9))

## [1.6.98](https://github.com/deepmodeling/dflow/compare/v1.6.97...v1.6.98) (2023-03-28)


### Bug Fixes

* waiting old pod to be deleted before post the new pod in the replay ([afd92c7](https://github.com/deepmodeling/dflow/commit/afd92c7b3ad574aefa60fef01309290c507d7456))

## [1.6.97](https://github.com/deepmodeling/dflow/compare/v1.6.96...v1.6.97) (2023-03-25)


### Bug Fixes

* missing **kwargs in run_command ([a68c588](https://github.com/deepmodeling/dflow/commit/a68c58882b5d82978c3cca07f410b3f5cbe733fe))

## [1.6.96](https://github.com/deepmodeling/dflow/compare/v1.6.95...v1.6.96) (2023-03-25)


### Bug Fixes

* always deepcopy template before run ([af6b3b4](https://github.com/deepmodeling/dflow/commit/af6b3b466b1eb13ae1ebcbf97cd73967d087fcc7))

## [1.6.95](https://github.com/deepmodeling/dflow/compare/v1.6.94...v1.6.95) (2023-03-25)


### Bug Fixes

* workaround dpdispatcher will not generate task hash again after modifying task ([7c7a2f0](https://github.com/deepmodeling/dflow/commit/7c7a2f0331c8cbfa835a19335ff65b101d6f81e1))

## [1.6.94](https://github.com/deepmodeling/dflow/compare/v1.6.93...v1.6.94) (2023-03-24)


### Bug Fixes

* add print_oe to run_command ([f2099db](https://github.com/deepmodeling/dflow/commit/f2099dbc26e471207ef61625f476d5d9f475aebf))
* dir not exist when merge_sliced_step ([f2099db](https://github.com/deepmodeling/dflow/commit/f2099dbc26e471207ef61625f476d5d9f475aebf))

## [1.6.93](https://github.com/deepmodeling/dflow/compare/v1.6.92...v1.6.93) (2023-03-24)


### Bug Fixes

* do not find download file in local context ([566fff9](https://github.com/deepmodeling/dflow/commit/566fff954cc907a9f5ecda804544b36014a8d4c7))
* support for container template in dflow submit ([566fff9](https://github.com/deepmodeling/dflow/commit/566fff954cc907a9f5ecda804544b36014a8d4c7))

## [1.6.92](https://github.com/deepmodeling/dflow/compare/v1.6.91...v1.6.92) (2023-03-24)


### Bug Fixes

* add dflow submit ([f9b1569](https://github.com/deepmodeling/dflow/commit/f9b156986373f1f00d24e9a145fe704200766d89))
* parse Workflow from yaml ([f9b1569](https://github.com/deepmodeling/dflow/commit/f9b156986373f1f00d24e9a145fe704200766d89))
* skip existed dir when downloading in local context ([18ab3bc](https://github.com/deepmodeling/dflow/commit/18ab3bcad7426a3222896c5837c43aed7e2d8e21))

## [1.6.91](https://github.com/deepmodeling/dflow/compare/v1.6.90...v1.6.91) (2023-03-22)


### Bug Fixes

* local context of dispatcher does not support wildcard in backward files ([5a4566d](https://github.com/deepmodeling/dflow/commit/5a4566da63f5b8cc477453424dcada52f892d5b3))

## [1.6.90](https://github.com/deepmodeling/dflow/compare/v1.6.89...v1.6.90) (2023-03-21)


### Bug Fixes

* NoneType has no attribute output_parameter ([0243155](https://github.com/deepmodeling/dflow/commit/02431558bee0a44b10c8b2077d7d4a2b7ad5315c))

## [1.6.89](https://github.com/deepmodeling/dflow/compare/v1.6.88...v1.6.89) (2023-03-21)


### Bug Fixes

* key of merged sliced step conflicted with key of artifact in debug mode ([80589c9](https://github.com/deepmodeling/dflow/commit/80589c93deabd0d33be642add6adf91e2a4dc7d8))
* update tutorials ([a200bba](https://github.com/deepmodeling/dflow/commit/a200bbac76abc06d34e3f4be46c1fbfe65ea2b40))

## [1.6.88](https://github.com/deepmodeling/dflow/compare/v1.6.87...v1.6.88) (2023-03-21)


### Bug Fixes

* success_ratio with merge_sliced_step ([14d8860](https://github.com/deepmodeling/dflow/commit/14d8860370e3e839ab9af28322635d5c48456191))

## [1.6.87](https://github.com/deepmodeling/dflow/compare/v1.6.86...v1.6.87) (2023-03-20)


### Bug Fixes

* {{item}} in key when merge sliced step ([c7b3cb6](https://github.com/deepmodeling/dflow/commit/c7b3cb6e927f260522a4e0960285b21d4c73a9a6))
* overwrite sliced output parameter when merge sliced step ([c7b3cb6](https://github.com/deepmodeling/dflow/commit/c7b3cb6e927f260522a4e0960285b21d4c73a9a6))

## [1.6.86](https://github.com/deepmodeling/dflow/compare/v1.6.85...v1.6.86) (2023-03-19)


### Bug Fixes

* add command line tools ([0cf8155](https://github.com/deepmodeling/dflow/commit/0cf81552bccacf7fe97c7169c6d2fe5bcd3d061a))

## [1.6.85](https://github.com/deepmodeling/dflow/compare/v1.6.84...v1.6.85) (2023-03-17)


### Bug Fixes

* bug in slice super OP ([44b5be2](https://github.com/deepmodeling/dflow/commit/44b5be25f108e719a37ce17a6703d6fefbee737d))

## [1.6.84](https://github.com/deepmodeling/dflow/compare/v1.6.83...v1.6.84) (2023-03-17)


### Bug Fixes

* 'NoneType' object has no attribute 'register_workflow' ([e8a15a7](https://github.com/deepmodeling/dflow/commit/e8a15a75699ce51a4df1f8d110c27fecc1087ec5))

## [1.6.83](https://github.com/deepmodeling/dflow/compare/v1.6.82...v1.6.83) (2023-03-16)


### Bug Fixes

* add get_artifact_metadata to MetadataClient, init S3Artifact with urn ([32fa20d](https://github.com/deepmodeling/dflow/commit/32fa20d4fa99b31a00fe1c2a5850c9153cb1574e))
* dispatcher executor pass env var ARGO_TEMPLATE from local to remote ([32fa20d](https://github.com/deepmodeling/dflow/commit/32fa20d4fa99b31a00fe1c2a5850c9153cb1574e))

## [1.6.82](https://github.com/deepmodeling/dflow/compare/v1.6.81...v1.6.82) (2023-03-16)


### Bug Fixes

* add register_output_artifact for OP ([ce27d37](https://github.com/deepmodeling/dflow/commit/ce27d3741f655dab7c848908a9a31796d42a7839))
* update metadata client ([ce27d37](https://github.com/deepmodeling/dflow/commit/ce27d3741f655dab7c848908a9a31796d42a7839))

## [1.6.81](https://github.com/deepmodeling/dflow/compare/v1.6.80...v1.6.81) (2023-03-15)


### Bug Fixes

* add query_workflows and query_archived_workflows ([adf5d65](https://github.com/deepmodeling/dflow/commit/adf5d651a0040fa55456a67247b4d1d8a2e53932))
* submit a workflow with labels ([adf5d65](https://github.com/deepmodeling/dflow/commit/adf5d651a0040fa55456a67247b4d1d8a2e53932))

## [1.6.80](https://github.com/deepmodeling/dflow/compare/v1.6.79...v1.6.80) (2023-03-15)


### Bug Fixes

* support get item of artifact combined with Slices ([7455632](https://github.com/deepmodeling/dflow/commit/74556328bc15d9434f1e58be204062cd5130a9d8))

## [1.6.79](https://github.com/deepmodeling/dflow/compare/v1.6.78...v1.6.79) (2023-03-15)


### Bug Fixes

* restrict version of typeguard&lt;3 ([dba9359](https://github.com/deepmodeling/dflow/commit/dba9359b04aa3ca30bad2bed2033390fb120ac91))

## [1.6.78](https://github.com/deepmodeling/dflow/compare/v1.6.77...v1.6.78) (2023-03-15)


### Bug Fixes

* support get key in OP in debug mode ([1d3d4db](https://github.com/deepmodeling/dflow/commit/1d3d4db57a312bc90c7b5dcf3006756f28ae1d1e))
* support path slice for Steps/DAG ([1d3d4db](https://github.com/deepmodeling/dflow/commit/1d3d4db57a312bc90c7b5dcf3006756f28ae1d1e))

## [1.6.77](https://github.com/deepmodeling/dflow/compare/v1.6.76...v1.6.77) (2023-03-15)


### Bug Fixes

* copy bug in dispatcher executor ([9258223](https://github.com/deepmodeling/dflow/commit/9258223b120800edb4aa18b5a50b0c7d90e1d6d2))

## [1.6.76](https://github.com/deepmodeling/dflow/compare/v1.6.75...v1.6.76) (2023-03-14)


### Bug Fixes

* get step key or workflow name in OP ([c37c6e7](https://github.com/deepmodeling/dflow/commit/c37c6e7ee2ead36b7159620d7e7129627f4e4f94))

## [1.6.75](https://github.com/deepmodeling/dflow/compare/v1.6.74...v1.6.75) (2023-03-13)


### Bug Fixes

* a bug in assemble_path_nested_dict ([d56cef6](https://github.com/deepmodeling/dflow/commit/d56cef63b9090f44147d76bfc96f5c3446d0c9e4))
* add __add__ to ArgoVar ([d56cef6](https://github.com/deepmodeling/dflow/commit/d56cef63b9090f44147d76bfc96f5c3446d0c9e4))
* get item which is a parameter of artifact ([d56cef6](https://github.com/deepmodeling/dflow/commit/d56cef63b9090f44147d76bfc96f5c3446d0c9e4))
* pass ArgoVar to when ([d56cef6](https://github.com/deepmodeling/dflow/commit/d56cef63b9090f44147d76bfc96f5c3446d0c9e4))

## [1.6.74](https://github.com/deepmodeling/dflow/compare/v1.6.73...v1.6.74) (2023-03-10)


### Bug Fixes

* get item of artifact in debug mode ([48706b0](https://github.com/deepmodeling/dflow/commit/48706b0c521c733456683d390deb590425648de5))

## [1.6.73](https://github.com/deepmodeling/dflow/compare/v1.6.72...v1.6.73) (2023-03-09)


### Bug Fixes

* avoid repeated deepcopy ([4b651fe](https://github.com/deepmodeling/dflow/commit/4b651fe5eff9896fef9ca72bb212dd49922b3eae))

## [1.6.72](https://github.com/deepmodeling/dflow/compare/v1.6.71...v1.6.72) (2023-03-09)


### Bug Fixes

* support for pass items of artifact as arguments ([da9b75a](https://github.com/deepmodeling/dflow/commit/da9b75a96f4fd91f067c00b1089ba4450bc140e0))

## [1.6.71](https://github.com/deepmodeling/dflow/compare/v1.6.70...v1.6.71) (2023-03-07)


### Bug Fixes

* remove node name before replay a step ([5c53812](https://github.com/deepmodeling/dflow/commit/5c53812a48069823cddb155e9e922f85e691ed0d))

## [1.6.70](https://github.com/deepmodeling/dflow/compare/v1.6.69...v1.6.70) (2023-03-02)


### Bug Fixes

* pass backward_files to dispatcher Bohrium input_data ([e31e749](https://github.com/deepmodeling/dflow/commit/e31e749d58a104caf90993931524674bb6db54b4))

## [1.6.69](https://github.com/deepmodeling/dflow/compare/v1.6.68...v1.6.69) (2023-03-02)


### Bug Fixes

* clean up useless codes ([b908314](https://github.com/deepmodeling/dflow/commit/b908314e0226bfdcc6f483ef32ea1cb69230e836))

## [1.6.68](https://github.com/deepmodeling/dflow/compare/v1.6.67...v1.6.68) (2023-03-02)


### Bug Fixes

* behavior of directories when downloading sliced artifact ([f0ec731](https://github.com/deepmodeling/dflow/commit/f0ec731a55792513b8e6587ebab9778aa5978811))
* dynamically render if expression ([f0ec731](https://github.com/deepmodeling/dflow/commit/f0ec731a55792513b8e6587ebab9778aa5978811))
* warnings of unclosed socket ([f0ec731](https://github.com/deepmodeling/dflow/commit/f0ec731a55792513b8e6587ebab9778aa5978811))

## [1.6.67](https://github.com/deepmodeling/dflow/compare/v1.6.66...v1.6.67) (2023-03-01)


### Bug Fixes

* reusing sliced steps followed by reusing sliced step in the same group ([a5cdb3a](https://github.com/deepmodeling/dflow/commit/a5cdb3a9c1ec8d9b00eaac30004a8ab9f6a250c6))

## [1.6.66](https://github.com/deepmodeling/dflow/compare/v1.6.65...v1.6.66) (2023-03-01)


### Bug Fixes

* Can't get attribute 'try_to_execute' on Mac ([74d6841](https://github.com/deepmodeling/dflow/commit/74d6841b2c85aca57dd6b1dd5093e57d8df5c63c))
* context in debug mode ([74d6841](https://github.com/deepmodeling/dflow/commit/74d6841b2c85aca57dd6b1dd5093e57d8df5c63c))
* continue_on_success_ratio and continue_on_num_success in debug mode ([74d6841](https://github.com/deepmodeling/dflow/commit/74d6841b2c85aca57dd6b1dd5093e57d8df5c63c))

## [1.6.65](https://github.com/deepmodeling/dflow/compare/v1.6.64...v1.6.65) (2023-03-01)


### Bug Fixes

* add group to dynamic resource ([4b6ce4a](https://github.com/deepmodeling/dflow/commit/4b6ce4a492813156fb51ed06c21d108d71febafe))

## [1.6.64](https://github.com/deepmodeling/dflow/compare/v1.6.63...v1.6.64) (2023-02-28)


### Bug Fixes

* move debug tests to the directory tests ([c25f984](https://github.com/deepmodeling/dflow/commit/c25f984427bcb7372837cecadbde713e41f44f28))
* set node to phase running after replay a step ([c25f984](https://github.com/deepmodeling/dflow/commit/c25f984427bcb7372837cecadbde713e41f44f28))
* step.workflow is None in debug mode ([c25f984](https://github.com/deepmodeling/dflow/commit/c25f984427bcb7372837cecadbde713e41f44f28))
* use if_expression explicitly to ensure the same behavior in both default and debug modes ([c25f984](https://github.com/deepmodeling/dflow/commit/c25f984427bcb7372837cecadbde713e41f44f28))

## [1.6.63](https://github.com/deepmodeling/dflow/compare/v1.6.62...v1.6.63) (2023-02-28)


### Bug Fixes

* big parameter passed in debug mode ([c7a03a7](https://github.com/deepmodeling/dflow/commit/c7a03a79fb574d3d772d742df50b92f379428e19))

## [1.6.62](https://github.com/deepmodeling/dflow/compare/v1.6.61...v1.6.62) (2023-02-27)


### Bug Fixes

* remove workflow name from global outputs ([93487db](https://github.com/deepmodeling/dflow/commit/93487db1b07232b24f40503a386393da9be65ef9))
* replay of step ([93487db](https://github.com/deepmodeling/dflow/commit/93487db1b07232b24f40503a386393da9be65ef9))

## [1.6.61](https://github.com/deepmodeling/dflow/compare/v1.6.60...v1.6.61) (2023-02-24)


### Bug Fixes

* wrong value of output parameter of step ([bbbc6d4](https://github.com/deepmodeling/dflow/commit/bbbc6d4ac9a78d844736997d16e2a5e9a707f980))

## [1.6.60](https://github.com/deepmodeling/dflow/compare/v1.6.59...v1.6.60) (2023-02-24)


### Bug Fixes

* support for expressions in values of parameters ([902f4ed](https://github.com/deepmodeling/dflow/commit/902f4ed7185acd6db891cc0f80aba1721fad21ad))

## [1.6.59](https://github.com/deepmodeling/dflow/compare/v1.6.58...v1.6.59) (2023-02-24)


### Bug Fixes

* do not copy reused artifact for default ([2fa94ed](https://github.com/deepmodeling/dflow/commit/2fa94edbc6bb231d7c15c61970461be04ed42436))

## [1.6.58](https://github.com/deepmodeling/dflow/compare/v1.6.57...v1.6.58) (2023-02-23)


### Bug Fixes

* allow None in List[Path] when checking types of artifact ([b5b6033](https://github.com/deepmodeling/dflow/commit/b5b603349a80c62dfa7774f12460a369ae28b053))
* support for login with phone number for bohrium ([b5b6033](https://github.com/deepmodeling/dflow/commit/b5b603349a80c62dfa7774f12460a369ae28b053))

## [1.6.57](https://github.com/deepmodeling/dflow/compare/v1.6.56...v1.6.57) (2023-02-22)


### Bug Fixes

* add pre_script and post_script ([fa0319d](https://github.com/deepmodeling/dflow/commit/fa0319db9853c9a6e6d259275177cb595a0e810c))
* dflow_success_tag cannot stat in dispatcher executor ([fa0319d](https://github.com/deepmodeling/dflow/commit/fa0319db9853c9a6e6d259275177cb595a0e810c))

## [1.6.56](https://github.com/deepmodeling/dflow/compare/v1.6.55...v1.6.56) (2023-02-21)


### Bug Fixes

* create secert with http headers ([5f384cd](https://github.com/deepmodeling/dflow/commit/5f384cd4a549c277ce5352cb89699bca12ed2056))

## [1.6.55](https://github.com/deepmodeling/dflow/compare/v1.6.54...v1.6.55) (2023-02-21)


### Bug Fixes

* pass env vars in dispatcher executor ([806c0dd](https://github.com/deepmodeling/dflow/commit/806c0ddb8199a928c28641135c36be2d058eef0a))

## [1.6.54](https://github.com/deepmodeling/dflow/compare/v1.6.53...v1.6.54) (2023-02-21)


### Bug Fixes

* support for artifact with nested dict of path ([da78171](https://github.com/deepmodeling/dflow/commit/da78171e5eddfa855336a8d03fc59d1fd5675c18))

## [1.6.53](https://github.com/deepmodeling/dflow/compare/v1.6.52...v1.6.53) (2023-02-16)


### Bug Fixes

* bug of merge_sliced_step in debug mode ([b364277](https://github.com/deepmodeling/dflow/commit/b364277e17486d2920880689290108247f2e5edd))

## [1.6.52](https://github.com/deepmodeling/dflow/compare/v1.6.51...v1.6.52) (2023-02-16)


### Bug Fixes

* support for handling multi slices in one dispatcher job ([5de1157](https://github.com/deepmodeling/dflow/commit/5de1157b5c15fbc11281889f42024a3543c498d9))

## [1.6.51](https://github.com/deepmodeling/dflow/compare/v1.6.50...v1.6.51) (2023-02-16)


### Bug Fixes

* upgrade ([4ddab4c](https://github.com/deepmodeling/dflow/commit/4ddab4cfe393117c9b84f5b707fac3eefba21e87))

## [1.6.50](https://github.com/deepmodeling/dflow/compare/v1.6.49...v1.6.50) (2023-02-16)


### Bug Fixes

* big parameter string null bug ([f9925c2](https://github.com/deepmodeling/dflow/commit/f9925c2c6b8de435e0314b6011a8a24335e492cb))

## [1.6.50]

### Bug Fixes

* Support BigParameter default value on local machine

## [1.6.49](https://github.com/deepmodeling/dflow/compare/v1.6.48...v1.6.49) (2023-02-15)


### Bug Fixes

* deprecate lebesgue executor ([0a68cb9](https://github.com/deepmodeling/dflow/commit/0a68cb9663d320744c6d2f8ed435bae8e6a020b3))
* one task not failing the whole group when pool_size used ([0a68cb9](https://github.com/deepmodeling/dflow/commit/0a68cb9663d320744c6d2f8ed435bae8e6a020b3))

## [1.6.48](https://github.com/deepmodeling/dflow/compare/v1.6.47...v1.6.48) (2023-02-14)


### Bug Fixes

* direct jsonpickle.dumps for big parameter ([7e1a063](https://github.com/deepmodeling/dflow/commit/7e1a063fbcfdd7e4ddbcaff3e0b9f761f1fc720f))
* support for argo_len of big parameter ([7e1a063](https://github.com/deepmodeling/dflow/commit/7e1a063fbcfdd7e4ddbcaff3e0b9f761f1fc720f))

## [1.6.47](https://github.com/deepmodeling/dflow/compare/v1.6.46...v1.6.47) (2023-02-13)


### Bug Fixes

* add API for creating bohrium job group ID ([772ad4d](https://github.com/deepmodeling/dflow/commit/772ad4ddb0f89e2dde6c0a0a231fa7c944788e6e))
* process cannot pass dflow configs ([77febb9](https://github.com/deepmodeling/dflow/commit/77febb9c7d618bfd62cac8f8c504e8d707909196))
* support for expression of loop item ([12c58c9](https://github.com/deepmodeling/dflow/commit/12c58c9e6cc6caff593a3e524f4eb882d492561d))
* support for slicing big parameter ([772ad4d](https://github.com/deepmodeling/dflow/commit/772ad4ddb0f89e2dde6c0a0a231fa7c944788e6e))

## [1.6.46](https://github.com/deepmodeling/dflow/compare/v1.6.45...v1.6.46) (2023-02-10)


### Bug Fixes

* jsonpickle.loads failed in bohrium executor ([24a603e](https://github.com/deepmodeling/dflow/commit/24a603e9ac8b28e15dee27e2e767c3973de8c829))

## [1.6.45](https://github.com/deepmodeling/dflow/compare/v1.6.44...v1.6.45) (2023-02-10)


### Bug Fixes

* save key-id mapping for super OP ([fd18d0e](https://github.com/deepmodeling/dflow/commit/fd18d0efaa0679f9602515247ce4b6ce2173dbab))

## [1.6.44](https://github.com/deepmodeling/dflow/compare/v1.6.43...v1.6.44) (2023-02-09)


### Bug Fixes

* fix dispatcher bohrium cannot sync log ([119e91c](https://github.com/deepmodeling/dflow/commit/119e91c4ad629cf81457a60ca8fa8424f5301cd5))

## [1.6.43](https://github.com/deepmodeling/dflow/compare/v1.6.42...v1.6.43) (2023-02-09)


### Bug Fixes

* add comments to query functions ([fa92dce](https://github.com/deepmodeling/dflow/commit/fa92dce6d0b46f34601210de173400bed87a97c5))
* different behaviors of OSS client ([fa92dce](https://github.com/deepmodeling/dflow/commit/fa92dce6d0b46f34601210de173400bed87a97c5))

## [1.6.42](https://github.com/deepmodeling/dflow/compare/v1.6.41...v1.6.42) (2023-02-07)


### Bug Fixes

* let argument override default value of big parameter ([22db61b](https://github.com/deepmodeling/dflow/commit/22db61bf4e6cfa45603044f5f74749916836ddde))

## [1.6.41](https://github.com/deepmodeling/dflow/compare/v1.6.40...v1.6.41) (2023-02-06)


### Bug Fixes

* add API query_global_outputs ([b96922d](https://github.com/deepmodeling/dflow/commit/b96922dfe4d0d3b77067d35a43e3e739ad8687e7))
* prepend dflow_bigpar_ to global name of parameter saved as artifact ([b96922d](https://github.com/deepmodeling/dflow/commit/b96922dfe4d0d3b77067d35a43e3e739ad8687e7))

## [1.6.40](https://github.com/deepmodeling/dflow/compare/v1.6.39...v1.6.40) (2023-02-06)


### Bug Fixes

* downgrade for query_step_by_key ([8485582](https://github.com/deepmodeling/dflow/commit/8485582756e754af9496bc48362930f467de3db0))
* save key2id map in global outputs, add query_step_by_key ([af64ea0](https://github.com/deepmodeling/dflow/commit/af64ea06f190de3aa45de4c4483931f42b637622))
* support default value of big parameter ([af64ea0](https://github.com/deepmodeling/dflow/commit/af64ea06f190de3aa45de4c4483931f42b637622))

## [1.6.39](https://github.com/deepmodeling/dflow/compare/v1.6.38...v1.6.39) (2023-02-03)


### Bug Fixes

* support group_size for debug mode ([5adc44c](https://github.com/deepmodeling/dflow/commit/5adc44ce3411951699ae80b4225ec1af5bd3d32d))

## [1.6.38](https://github.com/deepmodeling/dflow/compare/v1.6.37...v1.6.38) (2023-02-03)


### Bug Fixes

* add workflow_annotations to global config ([594781f](https://github.com/deepmodeling/dflow/commit/594781fb640d36367914717e4c41408669ab4541))
* restrict jsonpickle==2.2.0 ([594781f](https://github.com/deepmodeling/dflow/commit/594781fb640d36367914717e4c41408669ab4541))

## [1.6.37](https://github.com/deepmodeling/dflow/compare/v1.6.36...v1.6.37) (2023-02-02)


### Bug Fixes

* set default mode to None for input artifacts ([477f9d6](https://github.com/deepmodeling/dflow/commit/477f9d63868a5822c40a44a954f0aa180b363305))

## [1.6.36](https://github.com/deepmodeling/dflow/compare/v1.6.35...v1.6.36) (2023-02-02)


### Bug Fixes

* set default mode to 755 for input artifacts ([275b03d](https://github.com/deepmodeling/dflow/commit/275b03dda2806fc2bc117eee1f6340351d9fb1f0))

## [1.6.35](https://github.com/deepmodeling/dflow/compare/v1.6.34...v1.6.35) (2023-02-01)


### Bug Fixes

* add group_size feature for slices ([374e244](https://github.com/deepmodeling/dflow/commit/374e244e1c099d7dac1d6e12301ac5ea08a0b4d9))

## [1.6.34](https://github.com/deepmodeling/dflow/compare/v1.6.33...v1.6.34) (2023-01-31)


### Bug Fixes

* add oss storage client ([70c8950](https://github.com/deepmodeling/dflow/commit/70c8950173ae1b519930c3941ca6c93c8f53e126))
* add warns for handling argo objects ([70c8950](https://github.com/deepmodeling/dflow/commit/70c8950173ae1b519930c3941ca6c93c8f53e126))
* support dict of path for artifact ([70c8950](https://github.com/deepmodeling/dflow/commit/70c8950173ae1b519930c3941ca6c93c8f53e126))

## [1.6.33](https://github.com/deepmodeling/dflow/compare/v1.6.32...v1.6.33) (2023-01-29)


### Bug Fixes

* add argument interactive to run_command ([f7bd903](https://github.com/deepmodeling/dflow/commit/f7bd903f4912f78a503798b4d4f6141bc3f88c85))

## [1.6.32](https://github.com/deepmodeling/dflow/compare/v1.6.31...v1.6.32) (2023-01-20)


### Bug Fixes

* sys.stdin.encoding -&gt; sys.stdout.encoding ([f531786](https://github.com/deepmodeling/dflow/commit/f531786ce0ebdabd7ceebf2766821587d0e932c1))
* workaround for unavailable exit code of Bohrium job; ([f531786](https://github.com/deepmodeling/dflow/commit/f531786ce0ebdabd7ceebf2766821587d0e932c1))

## [1.6.31](https://github.com/deepmodeling/dflow/compare/v1.6.30...v1.6.31) (2023-01-18)


### Bug Fixes

* use bash -ic instead of bash -lc ([280b7b1](https://github.com/deepmodeling/dflow/commit/280b7b13b024f8c0104fc185d6038d555bcfeac6))

## [1.6.30](https://github.com/deepmodeling/dflow/compare/v1.6.29...v1.6.30) (2023-01-17)


### Bug Fixes

* continue on number/ratio skip errors ([4b18efa](https://github.com/deepmodeling/dflow/commit/4b18efa1d42fdb7a78c3ff7e29aeebc0295bd998))

## [1.6.29](https://github.com/deepmodeling/dflow/compare/v1.6.28...v1.6.29) (2023-01-17)


### Bug Fixes

* add try_bash to run_command ([ae1b77c](https://github.com/deepmodeling/dflow/commit/ae1b77c2c7c6ef622a3661c8f95e4fbde8190ca1))

## [1.6.28](https://github.com/deepmodeling/dflow/compare/v1.6.27...v1.6.28) (2023-01-07)


### Bug Fixes

* add log to Bohrium dispatcher executor ([14e5c58](https://github.com/deepmodeling/dflow/commit/14e5c5850a76f9ef22ba96b1b440107eea588b8b))
* add retry to dispatcher executor ([14e5c58](https://github.com/deepmodeling/dflow/commit/14e5c5850a76f9ef22ba96b1b440107eea588b8b))

## [1.6.27](https://github.com/deepmodeling/dflow/compare/v1.6.26...v1.6.27) (2023-01-04)


### Bug Fixes

* continue_on_success_ratio used with executor ([e1f61ae](https://github.com/deepmodeling/dflow/commit/e1f61ae754fceb62ee3c284bcdf861dfb76f9a4b))

## [1.6.26](https://github.com/deepmodeling/dflow/compare/v1.6.25...v1.6.26) (2023-01-03)


### Bug Fixes

* duplicate template name when multiple continue_on_success_ratio used ([3187ac6](https://github.com/deepmodeling/dflow/commit/3187ac6a20a09ffe6b142867be278d55c037b2a8))
* enhance performance of querying and reusing ([3187ac6](https://github.com/deepmodeling/dflow/commit/3187ac6a20a09ffe6b142867be278d55c037b2a8))

## [1.6.25](https://github.com/deepmodeling/dflow/compare/v1.6.24...v1.6.25) (2022-12-31)


### Bug Fixes

* no share path for non-dp user ([ad71a77](https://github.com/deepmodeling/dflow/commit/ad71a7764156f4211b0d7640768caafdaef9e294))

## [1.6.24](https://github.com/deepmodeling/dflow/compare/v1.6.23...v1.6.24) (2022-12-30)


### Bug Fixes

* unclosed file ResourceWarning ([2e61ef1](https://github.com/deepmodeling/dflow/commit/2e61ef167a824785ee65572e1e5b67b4e89686c5))

## [1.6.23](https://github.com/deepmodeling/dflow/compare/v1.6.22...v1.6.23) (2022-12-28)


### Bug Fixes

* ArgoStep deepcopy input dict ([47ca63d](https://github.com/deepmodeling/dflow/commit/47ca63dfc7cceb75a206892fa158fd7391e99370))

## [1.6.22](https://github.com/deepmodeling/dflow/compare/v1.6.21...v1.6.22) (2022-12-28)


### Bug Fixes

* ArgoStep not idempotent ([ac255bb](https://github.com/deepmodeling/dflow/commit/ac255bb317c935bbc8cf4838841db784cd16fa76))

## [1.6.21](https://github.com/deepmodeling/dflow/compare/v1.6.20...v1.6.21) (2022-12-28)


### Bug Fixes

* ArgoStep not idempotent ([21e4628](https://github.com/deepmodeling/dflow/commit/21e462866bacdc0c5446a1f8ae7093bbd1dc336a))

## [1.6.20](https://github.com/deepmodeling/dflow/compare/v1.6.19...v1.6.20) (2022-12-27)


### Bug Fixes

* enhance query_step efficiency ([3c5bd34](https://github.com/deepmodeling/dflow/commit/3c5bd348f5e51544701e69f3a1743f4704767985))

## [1.6.19](https://github.com/deepmodeling/dflow/compare/v1.6.18...v1.6.19) (2022-12-27)


### Bug Fixes

* refresh token in tiefblue client ([ca81d25](https://github.com/deepmodeling/dflow/commit/ca81d2598d57cf152e11f1d2610e0748e9d03237))
* remove empty step group ([ca81d25](https://github.com/deepmodeling/dflow/commit/ca81d2598d57cf152e11f1d2610e0748e9d03237))

## [1.6.18](https://github.com/deepmodeling/dflow/compare/v1.6.17...v1.6.18) (2022-12-20)


### Bug Fixes

* output parameter has no attribute path ([95920d3](https://github.com/deepmodeling/dflow/commit/95920d3b6c33921548affa3f308e4189eb4bf89e))

## [1.6.17](https://github.com/deepmodeling/dflow/compare/v1.6.16...v1.6.17) (2022-12-15)


### Bug Fixes

* dispatcher bohrium use bohrium.config ([3f3062b](https://github.com/deepmodeling/dflow/commit/3f3062b038715fe026e0cf67d168ce6e02f4bf30))
* executor used for context ([3f3062b](https://github.com/deepmodeling/dflow/commit/3f3062b038715fe026e0cf67d168ce6e02f4bf30))

## [1.6.16](https://github.com/deepmodeling/dflow/compare/v1.6.15...v1.6.16) (2022-12-15)


### Bug Fixes

* support for config from env var ([1fff9f2](https://github.com/deepmodeling/dflow/commit/1fff9f2b5f238f3d4161ce0676960b40a820596e))

## [1.6.15](https://github.com/deepmodeling/dflow/compare/v1.6.14...v1.6.15) (2022-12-14)


### Bug Fixes

* **path on windows:** use raw string to make the cross-platform path behaviors right. ([0b28521](https://github.com/deepmodeling/dflow/commit/0b2852181567e787b2d0b5fe197e521b9485c988))

## [1.6.14](https://github.com/deepmodeling/dflow/compare/v1.6.13...v1.6.14) (2022-12-09)


### Bug Fixes

* remove unecessary **kwargs ([35f1dee](https://github.com/deepmodeling/dflow/commit/35f1dee34ef7c58e45bd464e5b5f5a51532e5165))
* support for registering first slice only in lineage ([35f1dee](https://github.com/deepmodeling/dflow/commit/35f1dee34ef7c58e45bd464e5b5f5a51532e5165))
* support storage to argo gateway ([4ba49f2](https://github.com/deepmodeling/dflow/commit/4ba49f2b2a2324644d1ade256a539ff8508142ee))

## [1.6.13](https://github.com/deepmodeling/dflow/compare/v1.6.12...v1.6.13) (2022-12-08)


### Bug Fixes

* add HTTP headers to config ([a2573ff](https://github.com/deepmodeling/dflow/commit/a2573ffb962bee56c43cc64902668fdf13245c41))
* create secret for env var ([547dcaa](https://github.com/deepmodeling/dflow/commit/547dcaaa3625111ecbdc7b1bc3c0db879bc69fb5))
* support for env from a source ([12cd852](https://github.com/deepmodeling/dflow/commit/12cd8526592c680d267ccfcf501351b35f910faa))
* support for treating input artifact as non-archived file ([a2573ff](https://github.com/deepmodeling/dflow/commit/a2573ffb962bee56c43cc64902668fdf13245c41))

## [1.6.12](https://github.com/deepmodeling/dflow/compare/v1.6.11...v1.6.12) (2022-12-04)


### Bug Fixes

* support Steps template for continue_on_num_success and continue_on_success_ratio ([d1ce485](https://github.com/deepmodeling/dflow/commit/d1ce48529dc9cb6439610347542b2ee49f33d394))

## [1.6.11](https://github.com/deepmodeling/dflow/compare/v1.6.10...v1.6.11) (2022-12-02)


### Bug Fixes

* add extra prefixes ignored by S3Artifact auto-prefixing ([2e3ce02](https://github.com/deepmodeling/dflow/commit/2e3ce023044da8c11bbe1cf7bc045a0cb17f0c38))
* replace github link with gitee link in install-*.sh ([2e3ce02](https://github.com/deepmodeling/dflow/commit/2e3ce023044da8c11bbe1cf7bc045a0cb17f0c38))
* support for pass list of artifacts to input artifact ([b12c62e](https://github.com/deepmodeling/dflow/commit/b12c62e6c5ad16c0b9beec4c3d668e5e2a8d1eb5))

## [1.6.10](https://github.com/deepmodeling/dflow/compare/v1.6.9...v1.6.10) (2022-11-30)


### Bug Fixes

* add debug info for workflow manifest ([5ca6fa7](https://github.com/deepmodeling/dflow/commit/5ca6fa7230d286b596685ce99bf859c3c18f60af))
* add if __name__ == '__main__': to Python OP ([5ca6fa7](https://github.com/deepmodeling/dflow/commit/5ca6fa7230d286b596685ce99bf859c3c18f60af))
* add to_dict, to_json, to_yaml methods to workflow ([56ccf13](https://github.com/deepmodeling/dflow/commit/56ccf137b3029138efc5f09545f28ec714039e4a))
* find function OPs ([56ccf13](https://github.com/deepmodeling/dflow/commit/56ccf137b3029138efc5f09545f28ec714039e4a))

## [1.6.9](https://github.com/deepmodeling/dflow/compare/v1.6.8...v1.6.9) (2022-11-21)


### Bug Fixes

* use render_script method to map /tmp to /Users/x.liu/workflows/dflow/tmp for PythonOPTemplate ([77a50a6](https://github.com/deepmodeling/dflow/commit/77a50a6c0ac2bdec1faba73ec3a6f663e737a27e))

## [1.6.8](https://github.com/deepmodeling/dflow/compare/v1.6.7...v1.6.8) (2022-11-21)


### Bug Fixes

* bohrium in dispatcher executor ([2c19211](https://github.com/deepmodeling/dflow/commit/2c192114e475c580897a46df19cf3407caf1ba9b))

## [1.6.7](https://github.com/deepmodeling/dflow/compare/v1.6.6...v1.6.7) (2022-11-18)


### Bug Fixes

* add host addr for lebesgue executor ([d57b425](https://github.com/deepmodeling/dflow/commit/d57b4250f2d4a14fb76ad361320087911c870d18))
* make OP function callable ([d57b425](https://github.com/deepmodeling/dflow/commit/d57b4250f2d4a14fb76ad361320087911c870d18))

## [1.6.6](https://github.com/deepmodeling/dflow/compare/v1.6.5...v1.6.6) (2022-11-18)


### Bug Fixes

* add argo_sum and argo_concat ([487349f](https://github.com/deepmodeling/dflow/commit/487349f6d696a4dbf3b7efce4440b66aaa7338dc))
* add register_output_artifacts for step ([e047cf4](https://github.com/deepmodeling/dflow/commit/e047cf41dba7b919f7b42343f69f1344a83c8775))
* create secret for private registry ([e047cf4](https://github.com/deepmodeling/dflow/commit/e047cf41dba7b919f7b42343f69f1344a83c8775))
* debug mode: mimic argo's behavior on output parameter of parallel steps ([35f7f99](https://github.com/deepmodeling/dflow/commit/35f7f997c8e95f1ac3d95b8e2ba87215617b24d3))
* enhance error message of bohrium client ([615f4c0](https://github.com/deepmodeling/dflow/commit/615f4c03cbb3f876bd6091f5e22e1eb3b2ad9410))
* enhance function OP ([6c92799](https://github.com/deepmodeling/dflow/commit/6c9279938cde2904c4b8ccf27902728dc9ec8676))
* no prefix when user use S3Artifact() ([7d17af3](https://github.com/deepmodeling/dflow/commit/7d17af3ba0a039b3c8b5cd8cca0e9dd3f016c82a))
* support for always passing root path of artifact ([e9257fa](https://github.com/deepmodeling/dflow/commit/e9257faae5449f9821f7b8f04d8e1a39bf6d39da))

## [1.6.5](https://github.com/deepmodeling/dflow/compare/v1.6.4...v1.6.5) (2022-11-11)


### Bug Fixes

* add download method to S3Artifact ([6c2150a](https://github.com/deepmodeling/dflow/commit/6c2150a7f3f2cfbb6f792ab36d472798ef0882f7))
* add to_dict and from_dict methods to S3Artifact ([e999917](https://github.com/deepmodeling/dflow/commit/e999917add6047898457d384f6846038a78ae3ab))
* bug in collecting output parameters of sliced step ([a84f840](https://github.com/deepmodeling/dflow/commit/a84f8401697b5200e55a6494cb5cb1e97214448a))
* download S3Artifact ([adfd046](https://github.com/deepmodeling/dflow/commit/adfd046dc35497986282ecf5c3f818ab73060928))
* support for setting bohrium url for bohrium executor ([a84f840](https://github.com/deepmodeling/dflow/commit/a84f8401697b5200e55a6494cb5cb1e97214448a))

## [1.6.4](https://github.com/deepmodeling/dflow/compare/v1.6.3...v1.6.4) (2022-11-04)


### Bug Fixes

* get k8s client when used ([c1b3470](https://github.com/deepmodeling/dflow/commit/c1b3470a09694430b47a42e9d535b273221887db))

## [1.6.3](https://github.com/deepmodeling/dflow/compare/v1.6.2...v1.6.3) (2022-11-04)


### Bug Fixes

* future len of input parameter ([7fd6f13](https://github.com/deepmodeling/dflow/commit/7fd6f13371e9e83add4228fd9f149bc6f9ad6318))

## [1.6.2](https://github.com/deepmodeling/dflow/compare/v1.6.1...v1.6.2) (2022-11-02)


### Bug Fixes

* parse repo info from configmap ([f1aab93](https://github.com/deepmodeling/dflow/commit/f1aab932550d3fcfb53706117a0c95e49d843a37))

## [1.6.1](https://github.com/deepmodeling/dflow/compare/v1.6.0...v1.6.1) (2022-11-01)


### Bug Fixes

* a bug in sliced super op ([e1bf3a0](https://github.com/deepmodeling/dflow/commit/e1bf3a044e33273031170bf873227ccd3de945f4))
* add bohrium storage client ([8c7092c](https://github.com/deepmodeling/dflow/commit/8c7092c65b5f4ca3260fc46c0624f8f3b45c924a))
* support for sliced python op in sliced super op ([e1bf3a0](https://github.com/deepmodeling/dflow/commit/e1bf3a044e33273031170bf873227ccd3de945f4))
* support for storage plugins ([8c7092c](https://github.com/deepmodeling/dflow/commit/8c7092c65b5f4ca3260fc46c0624f8f3b45c924a))

## [1.6.0](https://github.com/deepmodeling/dflow/compare/v1.5.14...v1.6.0) (2022-10-26)


### Features

* introduce bohrium plugin which provide realtime log and adapt bohrium platform ([9296a3f](https://github.com/deepmodeling/dflow/commit/9296a3fecb8d5eb7ad30b573e7f58e57520aaa4a))


### Bug Fixes

* add artifact_repo_key ([0818d12](https://github.com/deepmodeling/dflow/commit/0818d1299fb3cc8f48a43102f268e8747bf3f918))
* slices for Steps/DAG ([0818d12](https://github.com/deepmodeling/dflow/commit/0818d1299fb3cc8f48a43102f268e8747bf3f918))

## [1.5.14](https://github.com/deepmodeling/dflow/compare/v1.5.13...v1.5.14) (2022-10-19)


### Bug Fixes

* add readme for debug mode ([151130c](https://github.com/deepmodeling/dflow/commit/151130c8d27ddc4928bc829ee963a3a013c91262))
* enhance error message ([f009607](https://github.com/deepmodeling/dflow/commit/f0096074d97343ad75646931aec2c3a1f28fb1ab))
* port-forward --address 0.0.0.0 in readme ([f009607](https://github.com/deepmodeling/dflow/commit/f0096074d97343ad75646931aec2c3a1f28fb1ab))
* slice by group in debug mode ([f009607](https://github.com/deepmodeling/dflow/commit/f0096074d97343ad75646931aec2c3a1f28fb1ab))

## [1.5.13](https://github.com/deepmodeling/dflow/compare/v1.5.12...v1.5.13) (2022-10-13)


### Bug Fixes

* support for python3.7 in debug mode ([6d7d971](https://github.com/deepmodeling/dflow/commit/6d7d9714bfec35e694ea401b940f00b555571583))

## [1.5.12](https://github.com/deepmodeling/dflow/compare/v1.5.11...v1.5.12) (2022-10-13)


### Bug Fixes

* optional input artifact in debug mode ([2eb90e8](https://github.com/deepmodeling/dflow/commit/2eb90e879f35f2a3181c8a2add503cc2005405b5))
* use subprocess.Popen in debug mode ([2eb90e8](https://github.com/deepmodeling/dflow/commit/2eb90e879f35f2a3181c8a2add503cc2005405b5))

## [1.5.11](https://github.com/deepmodeling/dflow/compare/v1.5.10...v1.5.11) (2022-10-13)


### Bug Fixes

* a typo ([c93235f](https://github.com/deepmodeling/dflow/commit/c93235f339edebe175897d545e17da1c72ed3840))
* add comments for config and s3_config ([358d4f1](https://github.com/deepmodeling/dflow/commit/358d4f1e262ea422eef34cbe2da3ce0122f199fe))
* add pool_size for slices ([7fe9d8c](https://github.com/deepmodeling/dflow/commit/7fe9d8c1d9d4809dccc18e885f0bbce6af156ccc))
* add utils for find OPs in a package ([358d4f1](https://github.com/deepmodeling/dflow/commit/358d4f1e262ea422eef34cbe2da3ce0122f199fe))
* consistent APIs for default mode and debug mode ([2e8f5cf](https://github.com/deepmodeling/dflow/commit/2e8f5cf74e0f797e4031bdc4deca3e87102415b4))
* format error some lines are too long ([06f4dd5](https://github.com/deepmodeling/dflow/commit/06f4dd56d527390a103816af4542d488ed86780e))
* omit queue_name if it is None in dispatcher executor ([2438c6c](https://github.com/deepmodeling/dflow/commit/2438c6c0a0f416365ed429131dd69125d05696ff))
* pass n_total explicitly in continue_on_success_ratio ([2438c6c](https://github.com/deepmodeling/dflow/commit/2438c6c0a0f416365ed429131dd69125d05696ff))
* raise Exception when a parameter passed to a big parameter, vice versa ([2e8f5cf](https://github.com/deepmodeling/dflow/commit/2e8f5cf74e0f797e4031bdc4deca3e87102415b4))
* save info of Steps/DAG in debug mode ([93784c2](https://github.com/deepmodeling/dflow/commit/93784c23f7d102ea7424d43d6870697645136dd9))
* support for download slices and modify slices in debug mode ([fb1da44](https://github.com/deepmodeling/dflow/commit/fb1da441a131503bcdd0fb3474e409ffebb93a96))

## [1.5.10](https://github.com/deepmodeling/dflow/compare/v1.5.9...v1.5.10) (2022-10-03)


### Bug Fixes

* add reused keys to global outputs ([5ea6b53](https://github.com/deepmodeling/dflow/commit/5ea6b536e8e8326d3b1e7f726e71671602e2c9bf))
* print uid when submitting ([5ea6b53](https://github.com/deepmodeling/dflow/commit/5ea6b536e8e8326d3b1e7f726e71671602e2c9bf))

## [1.5.9](https://github.com/deepmodeling/dflow/compare/v1.5.8...v1.5.9) (2022-10-03)


### Bug Fixes

* add requests to dependencies ([ac2c7f4](https://github.com/deepmodeling/dflow/commit/ac2c7f4a945381f1bc62f2acf555a134aa10503c))
* bug of parallelism for sliced step with sequence ([0729d1e](https://github.com/deepmodeling/dflow/commit/0729d1e398baa9d82dd741b026f5c23e431a292d))

## [1.5.8](https://github.com/deepmodeling/dflow/compare/v1.5.7...v1.5.8) (2022-09-28)


### Bug Fixes

* raise FileNotFoundError when downloading an artifact without key ([615a934](https://github.com/deepmodeling/dflow/commit/615a934b6c40ee5400aa8cc810c30b72dbcde85e))
* replace python command to python3 ([9c6772a](https://github.com/deepmodeling/dflow/commit/9c6772a49ba86730c6db125d25547551971e64fe))
* save uid after submission ([c696f1d](https://github.com/deepmodeling/dflow/commit/c696f1dadd52691242c2ac8668c573bbb16358c4))
* some bugs of dispatcher executor ([9c6772a](https://github.com/deepmodeling/dflow/commit/9c6772a49ba86730c6db125d25547551971e64fe))
* support for local mode of dispatcher ([9c6772a](https://github.com/deepmodeling/dflow/commit/9c6772a49ba86730c6db125d25547551971e64fe))

## [1.5.7](https://github.com/deepmodeling/dflow/compare/v1.5.6...v1.5.7) (2022-09-24)


### Bug Fixes

* add image pull secrets for workflow ([df69681](https://github.com/deepmodeling/dflow/commit/df696817c9df3063a7a1740eefe20dcdde9a2bf4))
* refact FutureLen, add FutureRange ([99730e2](https://github.com/deepmodeling/dflow/commit/99730e2865236c9b6b46682fe629b10834e8d8ae))
* support for skipping same files while downloading ([df69681](https://github.com/deepmodeling/dflow/commit/df696817c9df3063a7a1740eefe20dcdde9a2bf4))

## [1.5.6](https://github.com/deepmodeling/dflow/compare/v1.5.5...v1.5.6) (2022-09-22)


### Bug Fixes

* add methods for OP to get s3 key/link of input/output artifacts ([8a12911](https://github.com/deepmodeling/dflow/commit/8a12911bbc4f451ef0d70345346acbe09430abf2))
* add slurm docker cluster for autotests ([ef60d79](https://github.com/deepmodeling/dflow/commit/ef60d79690db125a94f7c852686b8acb35ae4c0d))

## [1.5.5](https://github.com/deepmodeling/dflow/compare/v1.5.4...v1.5.5) (2022-09-20)


### Bug Fixes

* pass steps/tasks in the initialization of Steps/DAG ([9ef5fd7](https://github.com/deepmodeling/dflow/commit/9ef5fd7a1d1c2c4fd52cc6952d5655020d7760e1))
* prepare_step is None ([9ef5fd7](https://github.com/deepmodeling/dflow/commit/9ef5fd7a1d1c2c4fd52cc6952d5655020d7760e1))

## [1.5.4](https://github.com/deepmodeling/dflow/compare/v1.5.3...v1.5.4) (2022-09-19)


### Bug Fixes

* support parallelism for a parallel step other than sliced step ([d62de45](https://github.com/deepmodeling/dflow/commit/d62de45cc8d21fbd0143fc156fad187ac0bcdf2e))

## [1.5.3](https://github.com/deepmodeling/dflow/compare/v1.5.2...v1.5.3) (2022-09-19)


### Bug Fixes

* support for any private key file name ([ded49c9](https://github.com/deepmodeling/dflow/commit/ded49c9ef06a946d9082680dbced795c07f8ab07))

## [1.5.2](https://github.com/deepmodeling/dflow/compare/v1.5.1...v1.5.2) (2022-09-18)


### Bug Fixes

* add parallelism for sliced step ([e620285](https://github.com/deepmodeling/dflow/commit/e620285ffaaaccf3250b53220fc33714681de69c))
* support dag of sliced tasks in debug mode ([bddfbac](https://github.com/deepmodeling/dflow/commit/bddfbaca77b4dd4cc664726d50feb314c3531e96))
* support debug mode for executor ([2cfc37b](https://github.com/deepmodeling/dflow/commit/2cfc37bd48d3649da8e7f336d4e3a53e6c7223b7))
* use process instead of thread ([2612f6e](https://github.com/deepmodeling/dflow/commit/2612f6eeadb73e3488d82342bd3311d46e6a8c3f))
* wait process by queue.get() ([ff27daf](https://github.com/deepmodeling/dflow/commit/ff27daff693d9643f4eb9402f660c0262a798d82))

## [1.5.1](https://github.com/deepmodeling/dflow/compare/v1.5.0...v1.5.1) (2022-09-16)


### Bug Fixes

* mixed mode for lebesgue executor ([9fe9490](https://github.com/deepmodeling/dflow/commit/9fe9490e7e52bddb361a78aea79c5875ecab8f75))

## [1.5.0](https://github.com/deepmodeling/dflow/compare/v1.4.0...v1.5.0) (2022-09-07)


### Features

* **syntax-sugar:** Offer `with` context syntax for workflow, dag. ([898d4e3](https://github.com/deepmodeling/dflow/commit/898d4e3e509acba3c1dfaa0ce376e54a7a3ab64f))


### Bug Fixes

* can set slices for PythonOPTemplate after initialization ([81a1f43](https://github.com/deepmodeling/dflow/commit/81a1f436c3ff0a394e0bcfdeadbe179185c8ec95))
* pass save_as_aritfact for value_from_expression ([26cb790](https://github.com/deepmodeling/dflow/commit/26cb790bdd0faabf9825427dfa89fa2bcc2023cc))
* remove duplicate export class: S3Artifact ([5f4198d](https://github.com/deepmodeling/dflow/commit/5f4198d18a720dd03f6f1b5685e3da170ee6facb))
* restore availability of download_sliced_output_artifact ([9441971](https://github.com/deepmodeling/dflow/commit/944197122b4aa2de1051442b5a018f3616fce0b5))

## [1.4.0](https://github.com/deepmodeling/dflow/compare/v1.3.1...v1.4.0) (2022-09-04)


### Features

* expose plugin dependencies class and utils for better extensibility ([5a0c349](https://github.com/deepmodeling/dflow/commit/5a0c3498d473a2ec734136bdcab1839e9845a5e1))


### Bug Fixes

* a bug of handling multiple big parameters ([e8c35c1](https://github.com/deepmodeling/dflow/commit/e8c35c134d6196f7db39ff7c45ab7835c2d13628))
* add parallelism to steps and dag ([dc3ec98](https://github.com/deepmodeling/dflow/commit/dc3ec98c1424f52515a41da58a586ffa0555c424))
* avoid double rendering of output parameter which refers to the input parameter of the same template ([96a4e2e](https://github.com/deepmodeling/dflow/commit/96a4e2ef24acfab8977b846c8543f245eb678d94))
* decrease time cost of query keys ([d546ad5](https://github.com/deepmodeling/dflow/commit/d546ad535d3eda29e36494885f49a8ddf1bb6491))

## [1.3.1](https://github.com/deepmodeling/dflow/compare/v1.3.0...v1.3.1) (2022-09-01)


### Bug Fixes

* __getitem__ of ArgoVar handle non-string items ([08f4336](https://github.com/deepmodeling/dflow/commit/08f4336b70fb0ccb514898ef2e4950b4e7cc22bb))
* add method render_script to PythonOPTemplate ([8b2cb4d](https://github.com/deepmodeling/dflow/commit/8b2cb4def78f6ca4d4872c733239a7e7675bb4b5))
* add pod GC strategy ([4b85f90](https://github.com/deepmodeling/dflow/commit/4b85f904fffaee1e226238945320ae84810fc516))
* skip uploading non-existing files in dispatcher executor ([65b7730](https://github.com/deepmodeling/dflow/commit/65b773005b2cc7c569f3cd9b62685fc5dca097ad))

## [1.3.0](https://github.com/deepmodeling/dflow/compare/v1.2.7...v1.3.0) (2022-08-10)


### Features

* **Init Container:** Support init_container in op_template. ([77264b2](https://github.com/deepmodeling/dflow/commit/77264b259c383bcb90ed16e6b425efb649a482dc))
* **Ray Executor:** Ray executor with dependencies settings. ([7695ad8](https://github.com/deepmodeling/dflow/commit/7695ad8e66048769071aab77791b78105d58674d))


### Bug Fixes

* mkdir return 0 and upload failed ([71bd31b](https://github.com/deepmodeling/dflow/commit/71bd31bc19d8aa7ff6e99d8100e96253d2c28676))
* update latest yaml ([be88142](https://github.com/deepmodeling/dflow/commit/be881424320f65c0a8b25ffeb458b5fc3d58ebf2))

## [1.2.7](https://github.com/deepmodeling/dflow/compare/v1.2.6...v1.2.7) (2022-08-07)


### Bug Fixes

* add image_pull_policy for util images ([d08c0ac](https://github.com/deepmodeling/dflow/commit/d08c0ac38ffef7216bbbc7de1c2e07f219fda5bf))

## [1.2.6](https://github.com/deepmodeling/dflow/compare/v1.2.5...v1.2.6) (2022-08-05)


### Bug Fixes

* add sub_path and slice to download_artifact ([de9148b](https://github.com/deepmodeling/dflow/commit/de9148b3c6e9e432c1dfbca7a17b4e3ddd39d5bb))
* data persistent for minio ([de9148b](https://github.com/deepmodeling/dflow/commit/de9148b3c6e9e432c1dfbca7a17b4e3ddd39d5bb))
* handle big parameters of failed step ([de9148b](https://github.com/deepmodeling/dflow/commit/de9148b3c6e9e432c1dfbca7a17b4e3ddd39d5bb))

## [1.2.5](https://github.com/deepmodeling/dflow/compare/v1.2.4...v1.2.5) (2022-08-03)


### Bug Fixes

* add envs to script op template ([8ef468a](https://github.com/deepmodeling/dflow/commit/8ef468ad05fb52889f61e581b523f853191db411))
* add workflow actions: terminate, delete, resubmit, resume, retry, stop, suspend ([8ef468a](https://github.com/deepmodeling/dflow/commit/8ef468ad05fb52889f61e581b523f853191db411))

## [1.2.4](https://github.com/deepmodeling/dflow/compare/v1.2.3...v1.2.4) (2022-08-01)


### Bug Fixes

* add type to query conditions of workflow steps ([7528151](https://github.com/deepmodeling/dflow/commit/7528151db4d22cb0f4d96b0cf97668e42d2fe21d))
* avoid variable expansions in cat EOF ([7528151](https://github.com/deepmodeling/dflow/commit/7528151db4d22cb0f4d96b0cf97668e42d2fe21d))
* decoding error when read source file of OP ([7528151](https://github.com/deepmodeling/dflow/commit/7528151db4d22cb0f4d96b0cf97668e42d2fe21d))
* merge envs in dispatcher executor ([7528151](https://github.com/deepmodeling/dflow/commit/7528151db4d22cb0f4d96b0cf97668e42d2fe21d))

## [1.2.3](https://github.com/deepmodeling/dflow/compare/v1.2.2...v1.2.3) (2022-07-27)


### Bug Fixes

* bugs of reuse ([5290065](https://github.com/deepmodeling/dflow/commit/529006511913558b98fe717c2d5f3a13865a6d3a))
* github action of building docker image fails ([e40ac52](https://github.com/deepmodeling/dflow/commit/e40ac521f5a1c18f47f5370d4977d32d9459d20f))

## [1.2.2](https://github.com/deepmodeling/dflow/compare/v1.2.1...v1.2.2) (2022-07-27)


### Bug Fixes

* call ArgoWorkflow.get_step for multiple times ([450cd16](https://github.com/deepmodeling/dflow/commit/450cd16cde9ca31b4701b04ab241f45d7fbc6d85))
* change query step by name from fuzzy query to exact query ([450cd16](https://github.com/deepmodeling/dflow/commit/450cd16cde9ca31b4701b04ab241f45d7fbc6d85))
* **IfExpression:** transfer to right string. ([aee507f](https://github.com/deepmodeling/dflow/commit/aee507f4ea1e7a3c98074edf5d21e5a8db7a7820))
* RFC 1123 of step name ([450cd16](https://github.com/deepmodeling/dflow/commit/450cd16cde9ca31b4701b04ab241f45d7fbc6d85))
* save each reused step into a single configmap to avoid 1MB limit ([450cd16](https://github.com/deepmodeling/dflow/commit/450cd16cde9ca31b4701b04ab241f45d7fbc6d85))
* support for query step by a list of conditions ([450cd16](https://github.com/deepmodeling/dflow/commit/450cd16cde9ca31b4701b04ab241f45d7fbc6d85))

## [1.2.1](https://github.com/deepmodeling/dflow/compare/v1.2.0...v1.2.1) (2022-07-24)


### Bug Fixes

* fix a bug of Path(None) ([0920062](https://github.com/deepmodeling/dflow/commit/09200622f236872f023667c899539cef594bd713))

## [1.2.0](https://github.com/deepmodeling/dflow/compare/v1.1.20...v1.2.0) (2022-07-24)


### Features

* add developer guide ([93f161d](https://github.com/deepmodeling/dflow/commit/93f161d520333538f6193d9f1a39235f4dde9862))
* add server-side installation script for Linux ([93f161d](https://github.com/deepmodeling/dflow/commit/93f161d520333538f6193d9f1a39235f4dde9862))
* make ArgoVar uniterable ([93f161d](https://github.com/deepmodeling/dflow/commit/93f161d520333538f6193d9f1a39235f4dde9862))


### Bug Fixes

* cannot pickle types in typing ([691dc57](https://github.com/deepmodeling/dflow/commit/691dc57163844627e89a7e75582141770c194bb4))
* fix a bug of path on Windows ([93f161d](https://github.com/deepmodeling/dflow/commit/93f161d520333538f6193d9f1a39235f4dde9862))
* handle big parameter whose name changes ([7513567](https://github.com/deepmodeling/dflow/commit/75135676452c4d1b028f4e4fd718e2e586f6a461))
* jsonize parameters before reusing ([7ff8272](https://github.com/deepmodeling/dflow/commit/7ff8272424c2a459bf6ba2165b6e49bde5d2bf22))
* line break in input parameter of Python OP ([ae8d11d](https://github.com/deepmodeling/dflow/commit/ae8d11d48d4dc9bbc9e9e815128e9f68eb752bdd))
* **readme:** fix import typo in README ([55f51a0](https://github.com/deepmodeling/dflow/commit/55f51a0c9f97cb7419ac01bd5e787df89aaa9f41))
* reused step does not have outputs ([8abb67d](https://github.com/deepmodeling/dflow/commit/8abb67dfd1df0de2427f1ed9390fde5529641fc5))
* step.outputs has no exitCode ([b98a635](https://github.com/deepmodeling/dflow/commit/b98a63597575f576af1cfd205019ced226c993b9))
* the conflict between input parameter of Python OP and dispatcher script ([c3981fb](https://github.com/deepmodeling/dflow/commit/c3981fbb191bbbedac20a3d8b7361e601c8307b3))

## 1.1.20

- add cloudpickle to dependencies
- add server-side installation script for Mac
- Lebesgue supports for mixed executor

## 1.1.19

- add container mode (docker, singularity or podman) to slurm remote executor, dispatcher executor and wlm executor.

## 1.1.18

- query archived workflows

## 1.1.17

- fit wlm for new features
- add __getitem__ to ArgoVar

## 1.1.16

- support for defining OP in the interactive mode (e.g. jupyter notebook)

## 1.1.15

- a catalog dir instead of catalog files for artifacts
- a better solution for subpath slices

## 1.1.14

- add save_path_as_artifact to handle large path lists

## 1.1.13

- improve uploading python packages
- compatible for python 3.5

## 1.1.12

- fix format problems
- add test examples
- copy_artifact supports for sort

## 1.1.11

### Added

- support for successive sub-path slices steps
- support for path of output artifact referring to path of input artifact in sub-path slices

## 1.1.10

### Added

- update path list of S3Artifact when used

## 1.1.9

### Added

- add type hints
- add interactive mode for Lebesgue's login
- add maximum parallelism for workflows
- add set_directory and run_command to utils

## 1.1.8

### Added

- modify the interface with Lebesgue

## 1.1.7

### Added

- add Parameter type sign for Python OP
- add username and password authentication for Lebesgue executor
- add global config archive_mode

### Fix

- fix: local config does not take effect for remote OP
- fix: dflow_dflow_private_key_path_list was not supplied

## 1.1.6

### Added

- support for DAG
- add catalog_file_name to configuration
- support for passing OP object instead of a derived class of OP to PythonOPTemplate
- add util_command argument to Step

## 1.1.5

### Added

- save path_list as parameter for each artifact
- add sub_path mode for slices

## 1.1.4

### Added

- add some verifications
- prevent mapping relative path repeatedly in dispatcher
- support for a sliced step outputing a list of paths with a single slice
- fix file processing on Windows
- modify interface of resource requests and limits

## 1.1.3

### Fix

- fix: the conflict between input parameter of Python OP and dispatcher script

## 1.1.2

### Fix

- fix: line break in input parameter of Python OP

## 1.1.1

### Added

- support for parallel step and sliced step

## 1.1.0

### Added

- support for using Python OP without dflow in the image

## 1.0.26

### Added

- fix a typo in io
- dicts override json_file in dispatcher executor
- allow for returning None for output artifact in OP
- work around Argo pod id != step id for slices and slurm job template

## 1.0.25

### Added

- support for id_rsa, id_dsa, id_ecdsa, id_ed25519

## 1.0.24

### Added

- fix \n in code for dispatcher executor
- handle io in slurm remote executor

## 1.0.23

### Added

- work around pod id != step id

### Fix

- fix: parameter has no attribute value

## 1.0.22

### Added

- map /tmp to pwd/tmp in slurm job

## 1.0.21

### Added

- add dispatcher executor
- with_param receives python list

## 1.0.20

### Fix

- fix: jsonize parameters before reusing

## 1.0.19

### Fix

- fix: handle big parameter whose name changes

## 1.0.18

### Added

- use str instead of jsonpickle to store parameter types

## 1.0.17

### Fix

- fix: cannot pickle types in typing

## 1.0.16

### Added

- fix a bug in 1.0.15
- record parameter type in parameter description

## 1.0.15

### Added

- handle big parameters in query step and reuse step

## 1.0.14

### Added

- name of OP template be optional
- add not allowed input artifact path
- not use pvc in slurm remote executor for default

## 1.0.13

### Added

- auto build docs to branch docs
- add retry for all actions in slurm remote executor
- support for use private key on node for SSH connection

## 1.0.12

### Added

- force lowercase for OP template to fix RFC 1123
- add private key option for SSH connection
- add container mode for remote Slurm executor
- add docs

## 1.0.11

### Added

- add global configurations
- modify lebesgue interfaces
- request kubernetes API server with token

## 1.0.10

### Added

- add Lebesgue plugins
- add resources requirements for templates
- support for slurm template for slices

## 1.0.9

### Fix

- fix a bug in sliced step

## 1.0.8

### Added

- handle empty sliced step

## 1.0.7

### Added

- add BigParameter
- retain empty dir
- optimize opening file descriptors

## 1.0.6

### Added

- add SlurmJobTemplate to submit slurm job by using wlm-operator

## 1.0.5

### Added

- download_artifact returns path list
- add convert_to_argo method to Workflow

## 1.0.4

### Added

- add resource template
- add some manifests

## 1.0.3

### Added

- add some arguments to PVC

## 1.0.2

### Fix

- restrict argo-workflows==5.0.0

## 1.0.1

### Added

- add comments doc

## 1.0.0

### Added

- initial release
