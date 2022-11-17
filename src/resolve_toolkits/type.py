class Folder:
    def GetName(self):
        ...

    def GetClipList(self):
        ...

    def GetSubFolderList(self):
        ...


class TimelineItem:
    def GetName(self) -> str:
        ...


class Timeline:
    def GetName(self) -> str:
        ...

    def GetItemListInTrack(
        self, trackType: str, index: int
    ) -> list[TimelineItem]:
        ...
