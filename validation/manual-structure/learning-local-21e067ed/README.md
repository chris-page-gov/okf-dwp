# Local learning-page check

The committed documentation at `21e067ed2f6be38892e99f199cceb3e1d5769664`
builds 172 source pages into 400 files. The existing renderer/browser regression
passes eight desktop/mobile interaction checks with no console errors.

The first attempt failed to launch Chrome within the process sandbox, before
any page check. Its original observation is retained. The permitted second
launch fulfils every request from the generated local files; it makes no public
site or external requests. This is not public deployment acceptance, a full
accessibility audit or a check of the later final documentation revision.
