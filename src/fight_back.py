class Participant:
    def __init__(self, name, PV, AC, active=False):
        self.name = name
        self.PV = PV
        self.max_pv = PV
        self.AC = AC
        self.active = active
        self.status: list[str] = []

    def setPV(self, pv):
        self.PV = pv

    def lines(self):
        yield f"{self.name} ({self.PV}/{self.max_pv}) \\{self.AC}/" + ":" if self.active else self.status[0]
        for status in self.status:
            yield status


class Fight:

    def __init__(self):
        self.participants: dict[int, list[Participant]] = {}
        self._len = 0

    def add(self, participant: Participant, initiative: int):
        self._len += 1
        if initiative in self.participants:
            self.participants[initiative].append(participant)
        else:
            self.participants[initiative] = [participant]

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
