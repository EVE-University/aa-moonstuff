class ScanParser:
    def __init__(self, scan_data: str):
        if "    " in scan_data:
            self.scan = self.__tabify(scan_data)
        else:
            self.scan = scan_data

    def __tabify(self, scan_data: str) -> str:
        """
        Converts quad-space separated data back to tab separated data.
        """
        return scan_data.replace("    ", "\t")

    def parse(self) -> dict:
        """
        Parses the scan into a dict that can then be processed.
        """
        ret = dict()

        # Split the scan into lines, ensure any CR characters are removed.
        scan_lines = self.scan.strip("\r").split("\n")

        # Remove any header lines (including moon names)
        scan_lines = list(line for line in scan_lines if "Moon" not in line)

        # Build dict of resources keyed to moon id
        for line in scan_lines:
            lst = line.split("\t")[1::]  # Trim off the leading blank space
            if len(line) < 6:
                raise Exception("The moonscan provided appears to be malformed.")
            moon_id = int(lst[-1])
            ore_id = int(lst[2])
            quantity = lst[1]
            if moon_id not in ret.keys():
                ret[moon_id] = list()
            ret[moon_id].append({"ore_id": ore_id, 'quantity': quantity, 'moon_id': moon_id})

        return ret

    def __str__(self) -> str:
        return self.scan

    def __repr__(self) -> str:
        return repr(self.scan)
