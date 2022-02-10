import typing


class Participant:
    def __init__(self, name, PV, AC, active=False):
        self.name = name
        self.PV = PV
        self.max_pv = PV
        self.AC = AC
        self.active = active
        self.status: list[str] = []
        self.initiative: int = 0

    def setPV(self, pv):
        self.PV = pv

    def lines(self):
        yield f"{self.name} ({self.PV}/{self.max_pv}) \\{self.AC}/ " + (":" if self.active else
                                                                        (self.status[0] if len(self.status) > 0
                                                                         else "")
                                                                        )
        if self.active:
            for status in self.status:
                yield status
        return


class Fight:

    def __init__(self):
        self.participants: dict[int, list[Participant]] = {}
        self._len = 0
        self.active_id = -1
        self.active_initiative = -1
        self.round = 0

    def add(self, participant: Participant, initiative: int):
        self._len += 1
        if initiative in self.participants:
            self.participants[initiative].append(participant)
        else:
            self.participants[initiative] = [participant]
        participant.initiative = initiative

    def __len__(self):
        return self._len

    def __iter__(self):
        ls = sorted(self.participants.keys(), reverse=True)
        for key in ls:
            for participant in self.participants[key]:
                yield participant

    def __getitem__(self, item: int):
        if item > self._len:
            raise IndexError(f"Participant index out of range [0, {self._len}]")
        ls = sorted(self.participants.keys(), reverse=True)
        count = 0
        for key in ls:
            for participant in self.participants[key]:
                count += 1
                if count > item:
                    return participant
        raise KeyError(f"Could not find object for key {item}")

    def __reversed__(self):
        ls = sorted(self.participants.keys())
        for key in ls:
            for participant in self.participants[key]:
                yield participant

    def begin(self):
        if self.active is not None:
            self.active.active = False
        self.active_id = 0
        self.active_initiative = max(self.participants.keys())
        self.active.active = True

    def next(self) -> str:
        """If the fight is not begun, then starts it.
        If it has, then moves turn to the next participant"""
        msg: str = ""
        if not self.has_begun:
            msg = "Began fight automatically"
            self.begin()
        else:
            if self.active_id < len(self.participants[self.active_initiative]) - 1:
                self.active_id += 1
            else:
                self.active_id = 0
                keys = self.participants.keys()
                if self.active_initiative == min(keys):
                    self.active_initiative = max(keys)
                    self.round += 1
                else:
                    inits = sorted((key for key in keys if key < self.active_initiative), reverse=True)
                    self.active_initiative = inits[0]

        return msg

    @property
    def has_begun(self) -> bool:
        return self.active is not None

    @property
    def active(self) -> typing.Optional[Participant]:
        if self.active_id < 0 or self.active_initiative < 0 or self.active_initiative not in self.participants:
            return None
        else:
            if self.active_id >= len(self.participants[self.active_id]):
                return None
            return self.participants[self.active_initiative][self.active_id]

    @active.setter
    def active(self, participant: Participant):
        for init in self.participants:
            for i in range(len(Ps := self.participants[init])):
                if Ps[i] == participant:
                    self.active_id = i
                    self.active_initiative = init
                    return
        raise ValueError("Could not find this item")
