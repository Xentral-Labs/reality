# Builder interfaces

`graph.format`: question → checked parameterized path and parameters. No business reads or writes.
`graph.interpret`: text, language, timezone → ready with validated question, or clarification/unsupported with explanation. Actor comes from existing caller context, never request arguments. Existing provider policies and usage reservation apply. No proposed business writes.
`graph.ask`: existing inputs and result plus generated editor representation. Canonical query echo is lossless.

Web adapters dispatch these shared tools. Examples use existing graph.templates and are not persisted on selection. Editor execution includes parameters. Sentence mode is enabled only when Plan can represent every query clause; otherwise expert query remains canonical.
