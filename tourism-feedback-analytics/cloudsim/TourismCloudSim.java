import java.util.*;
import org.cloudbus.cloudsim.*;
import org.cloudbus.cloudsim.core.CloudSim;
import org.cloudbus.cloudsim.provisioners.*;

/**
 * Simulates a cloud data centre processing tourism-feedback analysis jobs (cloudlets).
 * Usage: java TourismCloudSim <numVMs> <numJobs>   (CloudSim 3.0.3)
 */
public class TourismCloudSim {
    public static void main(String[] args) throws Exception {
        int numVms = args.length > 0 ? Integer.parseInt(args[0]) : 4;
        int numJobs = args.length > 1 ? Integer.parseInt(args[1]) : 40;

        CloudSim.init(1, Calendar.getInstance(), false);
        createDatacenter("Tourism_DC");
        DatacenterBroker broker = new DatacenterBroker("Broker");
        int id = broker.getId();

        List<Vm> vms = new ArrayList<>();
        for (int i = 0; i < numVms; i++)
            vms.add(new Vm(i, id, 1000, 1, 1024, 1000, 10000, "Xen", new CloudletSchedulerTimeShared()));
        broker.submitVmList(vms);

        UtilizationModel full = new UtilizationModelFull();
        List<Cloudlet> jobs = new ArrayList<>();
        for (int i = 0; i < numJobs; i++) {
            Cloudlet c = new Cloudlet(i, 40000 + (i % 5) * 10000, 1, 300, 300, full, full, full);
            c.setUserId(id);
            jobs.add(c);
        }
        broker.submitCloudletList(jobs);

        CloudSim.startSimulation();
        CloudSim.stopSimulation();

        List<Cloudlet> done = broker.getCloudletReceivedList();
        double max = 0, sum = 0;
        System.out.println("Job  Status   VM  Start   Finish");
        for (Cloudlet c : done) {
            System.out.printf("%-4d %-8s %-3d %-7.1f %.1f%n", c.getCloudletId(),
                    c.getStatus() == Cloudlet.SUCCESS ? "SUCCESS" : "FAILED", c.getVmId(),
                    c.getExecStartTime(), c.getFinishTime());
            max = Math.max(max, c.getFinishTime());
            sum += c.getActualCPUTime();
        }
        System.out.printf("%nVMs=%d Jobs=%d Makespan=%.1f s AvgCPUTime=%.1f s%n", numVms, done.size(), max, sum / done.size());
    }

    private static Datacenter createDatacenter(String name) throws Exception {
        List<Host> hosts = new ArrayList<>();
        for (int h = 0; h < 2; h++) {
            List<Pe> pes = new ArrayList<>();
            for (int p = 0; p < 4; p++) pes.add(new Pe(p, new PeProvisionerSimple(1000)));
            hosts.add(new Host(h, new RamProvisionerSimple(8192), new BwProvisionerSimple(100000),
                    1000000, pes, new VmSchedulerTimeShared(pes)));
        }
        DatacenterCharacteristics ch = new DatacenterCharacteristics("x86", "Linux", "Xen", hosts,
                10.0, 3.0, 0.05, 0.001, 0.0);
        return new Datacenter(name, ch, new VmAllocationPolicySimple(hosts), new LinkedList<Storage>(), 0);
    }
}
