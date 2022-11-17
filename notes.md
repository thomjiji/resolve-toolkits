how to get parent bin of the cam bin?

How to get only the Timeline under the current Day? Only Project.GetTimelineCount(), Project.GetTimelineByIndex(idx) two APIs.

`AddItemListToMediaPool()`'s API feature avoids repeated imports: As long as there is already clip A in the current bin, the clip A to be imported will be skipped, return a `[]`, otherwise return `[MediaPoolItem]`.
