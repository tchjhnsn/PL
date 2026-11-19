import Lake
open Lake DSL

package PatternLanguage where
  version := v!"0.0.0"

@[default_target]
lean_lib PatternLanguage where
  -- Build PatternLanguage.Language without a root PatternLanguage.lean file.
  globs := #[.submodules `PatternLanguage]
