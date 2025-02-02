import sys
import time
from datetime import timedelta
from pyopendds.Qos import DataWriterQos

from pyopendds import init_opendds, DomainParticipant, StatusKind, PyOpenDDS_Error

from pybasic.basic import Reading, ReadingKind

if __name__ == "__main__":
    try:
        # Initialize OpenDDS and Create DDS Entities
        init_opendds(opendds_debug_level=1)

        domain = DomainParticipant(34)
        topic = domain.create_topic("Readings", Reading)

        publisher = domain.create_publisher()
        datawriterqos = DataWriterQos()
        datawriterqos.history.depth = 2

        writer = publisher.create_datawriter(topic, qos=datawriterqos)

        # Wait for Subscriber to Connect
        print("Waiting for Subscriber...")
        print(timedelta(seconds=60))
        # writer.wait_for(StatusKind.PUBLICATION_MATCHED, timedelta(seconds=60))
        writer.wait_for(StatusKind.PUBLICATION_MATCHED, 0)
        print("Found subscriber!")

        sample = Reading()
        sample.kind = ReadingKind.acceleration
        sample.value = 123
        sample.where = "somewhere"

        time.sleep(1)
        # Read and Print Sample
        writer.write(sample)
        print("Done!")

    except PyOpenDDS_Error as e:
        sys.exit(e)
