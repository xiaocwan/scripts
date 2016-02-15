#!/bin/env python

import os, sys, re, time
import pipes
from subprocess import check_call,check_output,CalledProcessError
from ConfigParser import SafeConfigParser

config = SafeConfigParser()
class AOS(object):
    '''Make easier for OpenShift tests!'''

    osConfig = "./aos.conf"
    osUSer=""
    osPasswd=""
    masterUser=""
    master=""
    osProject=""
    masterConfigRoot=""
    masterConfigFile=""
    kubeConfigFile=""
    pemFile=""
    hawkularMetricsAppname=""
    kibanaOpsAppname=""
    kibanaAppname=""
    SAMetricsDeployer=""
    HCHStack=""
    imagePrefix=""
    imageVersion=""
    enablePV=""
    ESRam=""
    ESClusterSize=1
    EFKDeployer=""
    SSHIntoMaster=""

    @staticmethod
    def generate_default_config():
        '''Create the default config file if not exists'''

        config.add_section("master")
        config.add_section("project")
        config.add_section("image")
        config.add_section("ssh")
        config.set('project','os_user','chunchen')
        config.set('project','os_passwd','redhat')
        config.set('project','master_user','root')
        config.set('master','master','')
        config.set('master','master_config_root','/etc/origin/master')
        config.set('master','master_config_file','master-config.yaml')
        config.set('master','kube_config_file','admin.kubeconfig')
        config.set('ssh','pem_file','~/cfile/libra-new.pem')
        config.set('image','hawkular_metrics_appname','hawkular-metrics')
        config.set('image','kibana_ops_appname','kibana-ops')
        config.set('image','kibana_appname','kibana')
        config.set('image','serviceaccount_metrics_deployer','https://raw.githubusercontent.com/openshift/origin-metrics/master/metrics-deployer-setup.yaml')
        config.set('image','hch_stack','https://raw.githubusercontent.com/openshift/origin-metrics/master/metrics.yaml')
        config.set('image','image_prefix','rcm-img-docker01.build.eng.bos.redhat.com:5001/openshift3/')
        config.set('image','image_version','latest')
        config.set('image','enable_pv','False')
        config.set('image','elastic_ram','1024M')
        config.set('image','elastic_cluster_size','1')
        config.set('image','efk_deployer','https://raw.githubusercontent.com/openshift/origin-aggregated-logging/master/deployment/deployer.yaml')
        if not os.path.isfile(AOS.osConfig):
           with open(AOS.osConfig, 'wb') as defaultconfig:
               config.write(defaultconfig)

    @staticmethod
    def get_config():
        config.read(AOS.osConfig)
        AOS.osUser = config.get("project","os_user")
        AOS.osPasswd = config.get("project","os_passwd")
        AOS.masterUser = config.get("project","master_user")
        AOS.master = config.get("master","master")
        AOS.masterConfigRoot = config.get("master","master_config_root")
        AOS.masterConfigFile = config.get("master","master_config_file")
        AOS.kubeConfigFile = config.get("master","kube_config_file")
        AOS.pemFile = config.get("ssh","pem_file")
        AOS.hawkularMetricsAppname = config.get("image","hawkular_metrics_appname")
        AOS.kibanaOpsAppname = config.get("image","kibana_ops_appname")
        AOS.kibanaAppname = config.get("image","kibana_appname")
        AOS.SAMetricsDeployer = config.get("image","serviceaccount_metrics_deployer")
        AOS.HCHStack = config.get("image","hch_stack")
        AOS.imagePrefix = config.get("image","image_prefix")
        AOS.mageVersion = config.get("image","image_version")
        AOS.enablePV = config.getboolean("image","enable_pv")
        AOS.ESRam = config.get("image","elastic_ram")
        AOS.ESClusterSize = config.get("image","elastic_cluster_size")
        AOS.EFKDeployer = config.get("image","efk_deployer")
        AOS.SSHIntoMaster = "ssh -i %s -o identitiesonly=yes -o ConnectTimeout=10 %s@%s" % (os.path.expanduser(AOS.pemFile), AOS.masterUser, AOS.master)

    @staticmethod
    def echo_command(cmd="Please wait..."):
        print "[Running Command]:",cmd

    @staticmethod
    def echo(msg):
        print "[>>>>>>]:", msg

    @staticmethod
    def ssh_validation():
        try:
            command = "date > /dev/null"
            remote_command = '%s {}'.format(pipes.quote(command)) % AOS.SSHIntoMaster
            AOS.echo_command(remote_command)
            returncode = check_call(remote_command, shell=True,)
            return returncode
        except Exception, errMsg:
            os.sys.exit()

    @classmethod
    def check_validation(cls,):
        if not AOS.master:
            print "Please config '[master].master' under %s or specify OpenShift master via '-m' within command line!" % os.path.abspath(AOS.osConfig)
            os.sys.exit()

    @staticmethod
    def run_ssh_command(cmd, output=False, asShell=True,nossh=False):
        remote_command = '%s {}'.format(pipes.quote(cmd)) % AOS.SSHIntoMaster
        if nossh:
            remote_command = cmd
        try:
          if output:
            outputs = check_output(remote_command, shell=asShell)
            return outputs
          else:
            check_call(remote_command, shell=asShell)
        except CalledProcessError,msg:
            print type(msg),msg

    @classmethod
    def do_permission(cls,role_type,role_name,user,admin=False):

        pre_cmd = "oc policy"
        if admin:
            pre_cmd = "oadm policy"
        command = "%s %s %s %s" % (pre_cmd,role_type,role_name,user)
        AOS.run_ssh_command(command,nossh=admin)

    @classmethod
    def get_openshift_resource(cls,resource="pods",project=AOS.osProject):
        pass

    @classmethod
    def start_origin_openshift(cls):
        AOS.echo("Starting OpenShift Service...")
        outputs = AOS.run_ssh_command("openshift start --public-master=%s:8443 --write-config=/etc/origin" % AOS.master, output=True)
        nodeConfigPath = outputs.rstrip().split()[-1]
        nodeConfig = os.path.join(nodeConfigPath,"node-config.yaml")
        masterConfig = os.path.join(AOS.masterConfigRoot, AOS.masterConfigFile)
        kubeConfig = os.path.join(AOS.masterConfigRoot, AOS.kubeConfigFile)
        AOS.run_ssh_command("sed -i -e '/loggingPublicURL:/d' -e '/metricsPublicURL:/d' %s" % masterConfig)
        AOS.run_ssh_command("killall openshift")
        AOS.run_ssh_command("echo export KUBECONFIG=%s >> ~/.bashrc; nohup openshift start --node-config=%s --master-config=%s &> openshift.log &" % (kubeConfig,nodeConfig,masterConfig))
        AOS.echo("Wait 23 seconds for upping OpenShift...")
        time.sleep(23)
        # For automation cases related admin role
        master = AOS.master.replace('.','-')
        AOS.run_ssh_command("oc config use-context default/%s:8443/system:admin && mkdir -p /root/.kube && cp /etc/origin/master/admin.kubeconfig /root/.kube/config" % master)

    @staticmethod
    def create_default_pods():
        # Backup: --images='openshift/origin-${component}:latest
        AOS.run_ssh_command("oc delete dc --all -n default; oc delete rc --all -n default; oc delete pods --all -n default; oc delete svc --all -n default; oc delete is --all -n openshift")
        # Add permission for creating router
        AOS.run_ssh_command("oadm policy add-scc-to-user privileged system:serviceaccount:default:default")
        AOS.echo("Starting to create registry and router")
        AOS.run_ssh_command("export CURL_CA_BUNDLE=/etc/origin/master/ca.crt; \
                  chmod a+rwX /etc/origin/master/admin.kubeconfig; \
                  chmod +r /etc/origin/master/openshift-registry.kubeconfig; \
                  oadm registry --create --credentials=/etc/origin/master/openshift-registry.kubeconfig --config=/etc/origin/master/admin.kubeconfig; \
                  oadm  router --credentials=/etc/origin/master/openshift-router.kubeconfig --config=/etc/origin/master/admin.kubeconfig --service-account=default")

if __name__ == "__main__":
   AOS.generate_default_config()
   AOS.get_config()
   AOS.ssh_validation()
   AOS.check_validation()
   AOS.start_origin_openshift()