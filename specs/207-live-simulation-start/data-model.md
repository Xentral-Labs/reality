# Data model

No new tables or columns. ScheduledJob.configuration gains optional initial offset/anchor coordination metadata; ScheduledJobRun.configuration freezes an initial-occurrence marker. Existing tenant foreign keys, occurrence uniqueness, one unfinished run and queue capacity remain authoritative. Demo connection → current schedule is the shortest link. SourceRecord, Document, DocumentLine and Commitment are unchanged.
