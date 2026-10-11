#!/bin/bash
set -euo pipefail
umask 077
cat >/var/lib/p8-continuation/deployment/external-readiness-evidence.json <<'EVIDENCE'
{
  "aws-preflight-attempt1.json": {
    "sha256": "bb63cdaa7b83f6c50f0d997a896735e8e7d20e157ed8ce1e7e2d415fa93916d5",
    "result": {
      "content": [
        {
          "type": "text",
          "text": "{\"status\": \"success\", \"stdout\": \"\", \"stderr\": null, \"return_value\": {\"credits\": {\"accountId\": \"803656589923\", \"accountPlanType\": \"FREE\", \"accountPlanStatus\": \"ACTIVE\", \"accountPlanRemainingCredits\": {\"amount\": 119.37, \"unit\": \"USD\"}, \"accountPlanExpirationDate\": \"2027-04-05T13:45:14.308000+00:00\"}, \"old_host\": {\"Reservations\": [{\"ReservationId\": \"r-09dd2a8d6fada358a\", \"OwnerId\": \"803656589923\", \"Groups\": [], \"Instances\": [{\"Architecture\": \"x86_64\", \"BlockDeviceMappings\": [{\"DeviceName\": \"/dev/sda1\", \"Ebs\": {\"AttachTime\": \"2026-10-07T15:29:06+00:00\", \"DeleteOnTermination\": false, \"Status\": \"attached\", \"VolumeId\": \"vol-07baf9132bce08e77\", \"EbsCardIndex\": 0}}], \"ClientToken\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\", \"EbsOptimized\": false, \"EnaSupport\": true, \"Hypervisor\": \"xen\", \"IamInstanceProfile\": {\"Arn\": \"arn:aws:iam::803656589923:instance-profile/FYP-p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\", \"Id\": \"AIPA3WHNKMJRVRF7W6G3I\"}, \"NetworkInterfaces\": [{\"Attachment\": {\"AttachTime\": \"2026-10-07T15:29:05+00:00\", \"AttachmentId\": \"eni-attach-0813fcecf35d7cf54\", \"DeleteOnTermination\": true, \"DeviceIndex\": 0, \"Status\": \"attached\", \"NetworkCardIndex\": 0}, \"Description\": \"\", \"Groups\": [{\"GroupId\": \"sg-076d87ac5db0a6f52\", \"GroupName\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}], \"Ipv6Addresses\": [], \"MacAddress\": \"02:ff:c8:a3:48:07\", \"NetworkInterfaceId\": \"eni-0b2d2e6ce97e47a2f\", \"OwnerId\": \"803656589923\", \"PrivateDnsName\": \"ip-172-31-4-109.ap-southeast-2.compute.internal\", \"PrivateIpAddress\": \"172.31.4.109\", \"PrivateIpAddresses\": [{\"Primary\": true, \"PrivateDnsName\": \"ip-172-31-4-109.ap-southeast-2.compute.internal\", \"PrivateIpAddress\": \"172.31.4.109\"}], \"SourceDestCheck\": true, \"Status\": \"in-use\", \"SubnetId\": \"subnet-05c5c729c83dc651b\", \"VpcId\": \"vpc-0c74e59331cbc1caa\", \"InterfaceType\": \"interface\", \"Operator\": {\"Managed\": false}}], \"RootDeviceName\": \"/dev/sda1\", \"RootDeviceType\": \"ebs\", \"SecurityGroups\": [{\"GroupId\": \"sg-076d87ac5db0a6f52\", \"GroupName\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}], \"SourceDestCheck\": true, \"StateReason\": {\"Code\": \"Client.UserInitiatedShutdown\", \"Message\": \"Client.UserInitiatedShutdown: User initiated shutdown\"}, \"Tags\": [{\"Key\": \"research.owner\", \"Value\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}, {\"Key\": \"Name\", \"Value\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}, {\"Key\": \"research.stage\", \"Value\": \"8.5\"}], \"VirtualizationType\": \"hvm\", \"CpuOptions\": {\"CoreCount\": 1, \"ThreadsPerCore\": 2}, \"CapacityReservationSpecification\": {\"CapacityReservationPreference\": \"open\"}, \"HibernationOptions\": {\"Configured\": false}, \"MetadataOptions\": {\"State\": \"applied\", \"HttpTokens\": \"required\", \"HttpPutResponseHopLimit\": 1, \"HttpEndpoint\": \"enabled\", \"HttpProtocolIpv6\": \"disabled\", \"InstanceMetadataTags\": \"disabled\"}, \"EnclaveOptions\": {\"Enabled\": false}, \"BootMode\": \"uefi-preferred\", \"PlatformDetails\": \"Linux/UNIX\", \"UsageOperation\": \"RunInstances\", \"UsageOperationUpdateTime\": \"2026-10-07T15:29:05+00:00\", \"PrivateDnsNameOptions\": {\"HostnameType\": \"ip-name\", \"EnableResourceNameDnsARecord\": false, \"EnableResourceNameDnsAAAARecord\": false}, \"MaintenanceOptions\": {\"AutoRecovery\": \"default\", \"RebootMigration\": \"default\"}, \"CurrentInstanceBootMode\": \"uefi\", \"NetworkPerformanceOptions\": {\"BandwidthWeighting\": \"default\"}, \"Operator\": {\"Managed\": false, \"HiddenByDefault\": false}, \"InstanceId\": \"i-0a6196aff6f8098ac\", \"ImageId\": \"ami-090b1140798d2d006\", \"State\": {\"Code\": 80, \"Name\": \"stopped\"}, \"PrivateDnsName\": \"ip-172-31-4-109.ap-southeast-2.compute.internal\", \"PublicDnsName\": \"\", \"StateTransitionReason\": \"User initiated (2026-10-07 15:57:46 GMT)\", \"AmiLaunchIndex\": 0, \"ProductCodes\": [], \"InstanceType\": \"m7i-flex.large\", \"LaunchTime\": \"2026-10-07T15:29:05+00:00\", \"Placement\": {\"AvailabilityZoneId\": \"apse2-az1\", \"GroupName\": \"\", \"Tenancy\": \"default\", \"AvailabilityZone\": \"ap-southeast-2a\"}, \"Monitoring\": {\"State\": \"disabled\"}, \"SubnetId\": \"subnet-05c5c729c83dc651b\", \"VpcId\": \"vpc-0c74e59331cbc1caa\", \"PrivateIpAddress\": \"172.31.4.109\"}]}]}, \"old_disk\": {\"Volumes\": [{\"AvailabilityZoneId\": \"apse2-az1\", \"Iops\": 3000, \"Tags\": [{\"Key\": \"Name\", \"Value\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}, {\"Key\": \"research.owner\", \"Value\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}, {\"Key\": \"research.stage\", \"Value\": \"8.5\"}], \"VolumeType\": \"gp3\", \"MultiAttachEnabled\": false, \"Throughput\": 125, \"Operator\": {\"Managed\": false, \"HiddenByDefault\": false}, \"VolumeArn\": \"arn:aws:ec2:ap-southeast-2:803656589923:volume/vol-07baf9132bce08e77\", \"OwnerId\": \"803656589923\", \"VolumeId\": \"vol-07baf9132bce08e77\", \"Size\": 160, \"SnapshotId\": \"snap-04f8536d791ceaecf\", \"AvailabilityZone\": \"ap-southeast-2a\", \"State\": \"in-use\", \"CreateTime\": \"2026-10-07T15:29:06.157000+00:00\", \"Attachments\": [{\"DeleteOnTermination\": false, \"EbsCardIndex\": 0, \"VolumeId\": \"vol-07baf9132bce08e77\", \"InstanceId\": \"i-0a6196aff6f8098ac\", \"Device\": \"/dev/sda1\", \"State\": \"attached\", \"AttachTime\": \"2026-10-07T15:29:06+00:00\"}], \"Encrypted\": true, \"KmsKeyId\": \"arn:aws:kms:ap-southeast-2:803656589923:key/1ad9e0e5-ad7c-4f52-8b41-50c266898626\"}]}, \"image\": {\"Images\": [{\"PlatformDetails\": \"Linux/UNIX\", \"UsageOperation\": \"RunInstances\", \"BlockDeviceMappings\": [{\"Ebs\": {\"DeleteOnTermination\": true, \"SnapshotId\": \"snap-04f8536d791ceaecf\", \"VolumeSize\": 8, \"VolumeType\": \"gp3\", \"Encrypted\": false}, \"DeviceName\": \"/dev/sda1\"}, {\"DeviceName\": \"/dev/sdb\", \"VirtualName\": \"ephemeral0\"}, {\"DeviceName\": \"/dev/sdc\", \"VirtualName\": \"ephemeral1\"}], \"Description\": \"Canonical, Ubuntu, 24.04, amd64 noble image\", \"EnaSupport\": true, \"Hypervisor\": \"xen\", \"ImageOwnerAlias\": \"amazon\", \"Name\": \"ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-20260923\", \"RootDeviceName\": \"/dev/sda1\", \"RootDeviceType\": \"ebs\", \"SriovNetSupport\": \"simple\", \"VirtualizationType\": \"hvm\", \"BootMode\": \"uefi-preferred\", \"DeprecationTime\": \"2028-09-23T11:57:18.000Z\", \"ImdsSupport\": \"v2.0\", \"FreeTierEligible\": true, \"PublicSsmParameterName\": \"aws/service/canonical/ubuntu/server/noble/stable/current/amd64/hvm/ebs-gp3/ami-id\", \"ImageId\": \"ami-090b1140798d2d006\", \"ImageLocation\": \"amazon/ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-20260923\", \"State\": \"available\", \"OwnerId\": \"099720109477\", \"CreationDate\": \"2026-09-23T11:57:18.000Z\", \"Public\": true, \"Architecture\": \"x86_64\", \"ImageType\": \"machine\"}]}, \"subnet\": {\"Subnets\": [{\"AvailabilityZoneId\": \"apse2-az1\", \"MapCustomerOwnedIpOnLaunch\": false, \"OwnerId\": \"803656589923\", \"AssignIpv6AddressOnCreation\": false, \"Ipv6CidrBlockAssociationSet\": [], \"SubnetArn\": \"arn:aws:ec2:ap-southeast-2:803656589923:subnet/subnet-05c5c729c83dc651b\", \"EnableDns64\": false, \"Ipv6Native\": false, \"PrivateDnsNameOptionsOnLaunch\": {\"HostnameType\": \"ip-name\", \"EnableResourceNameDnsARecord\": false, \"EnableResourceNameDnsAAAARecord\": false}, \"BlockPublicAccessStates\": {\"InternetGatewayBlockMode\": \"off\"}, \"SubnetId\": \"subnet-05c5c729c83dc651b\", \"State\": \"available\", \"VpcId\": \"vpc-0c74e59331cbc1caa\", \"CidrBlock\": \"172.31.0.0/20\", \"AvailableIpAddressCount\": 4090, \"AvailabilityZone\": \"ap-southeast-2a\", \"DefaultForAz\": true, \"MapPublicIpOnLaunch\": true}]}, \"security\": {\"SecurityGroups\": [{\"GroupId\": \"sg-076d87ac5db0a6f52\", \"IpPermissionsEgress\": [{\"IpProtocol\": \"-1\", \"UserIdGroupPairs\": [], \"IpRanges\": [{\"CidrIp\": \"0.0.0.0/0\"}], \"Ipv6Ranges\": [], \"PrefixListIds\": []}], \"Tags\": [{\"Key\": \"research.owner\", \"Value\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}, {\"Key\": \"Name\", \"Value\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}, {\"Key\": \"research.stage\", \"Value\": \"8.5\"}], \"VpcId\": \"vpc-0c74e59331cbc1caa\", \"SecurityGroupArn\": \"arn:aws:ec2:ap-southeast-2:803656589923:security-group/sg-076d87ac5db0a6f52\", \"OwnerId\": \"803656589923\", \"GroupName\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\", \"Description\": \"Frozen Phase 8 serial research: SSM only, no inbound ports\", \"IpPermissions\": []}]}, \"routes\": {\"RouteTables\": [{\"Associations\": [{\"Main\": true, \"RouteTableAssociationId\": \"rtbassoc-0c98c36c2eac50733\", \"RouteTableId\": \"rtb-06ba3e3d927d5aea6\", \"AssociationState\": {\"State\": \"associated\"}}], \"PropagatingVgws\": [], \"RouteTableId\": \"rtb-06ba3e3d927d5aea6\", \"Routes\": [{\"DestinationCidrBlock\": \"172.31.0.0/16\", \"GatewayId\": \"local\", \"Origin\": \"CreateRouteTable\", \"State\": \"active\"}, {\"DestinationCidrBlock\": \"0.0.0.0/0\", \"GatewayId\": \"igw-05c25cbe2b04b9b01\", \"Origin\": \"CreateRoute\", \"State\": \"active\"}], \"Tags\": [], \"VpcId\": \"vpc-0c74e59331cbc1caa\", \"OwnerId\": \"803656589923\"}]}, \"profile\": {\"InstanceProfile\": {\"Path\": \"/\", \"InstanceProfileName\": \"FYP-p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\", \"InstanceProfileId\": \"AIPA3WHNKMJRVRF7W6G3I\", \"Arn\": \"arn:aws:iam::803656589923:instance-profile/FYP-p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\", \"CreateDate\": \"2026-10-07T15:25:44+00:00\", \"Roles\": [{\"Path\": \"/\", \"RoleName\": \"FYP-p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\", \"RoleId\": \"AROA3WHNKMJR4XAOKYDGF\", \"Arn\": \"arn:aws:iam::803656589923:role/FYP-p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\", \"CreateDate\": \"2026-10-07T15:25:43+00:00\", \"AssumeRolePolicyDocument\": {\"Version\": \"2012-10-17\", \"Statement\": [{\"Effect\": \"Allow\", \"Principal\": {\"Service\": \"ec2.amazonaws.com\"}, \"Action\": \"sts:AssumeRole\"}]}}], \"Tags\": [{\"Key\": \"research.owner\", \"Value\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}, {\"Key\": \"research.stage\", \"Value\": \"8.5\"}, {\"Key\": \"Name\", \"Value\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}]}}, \"versioning\": {\"Status\": \"Enabled\"}, \"price_compute\": {\"products\": [{\"product\": {\"productFamily\": \"Compute Instance\", \"attributes\": {\"enhancedNetworkingSupported\": \"Yes\", \"intelTurboAvailable\": \"Yes\", \"memory\": \"8 GiB\", \"dedicatedEbsThroughput\": \"Up to 10000 Mbps\", \"vcpu\": \"2\", \"classicnetworkingsupport\": \"false\", \"capacitystatus\": \"Used\", \"locationType\": \"AWS Region\", \"storage\": \"EBS only\", \"instanceFamily\": \"General purpose\", \"operatingSystem\": \"Linux\", \"intelAvx2Available\": \"Yes\", \"instanceFamilyCategory\": \"General Purpose\", \"regionCode\": \"ap-southeast-2\", \"physicalProcessor\": \"Intel Xeon Scalable (Sapphire Rapids)\", \"clockSpeed\": \"3.5 GHz\", \"ecu\": \"NA\", \"networkPerformance\": \"Up to 12500 Megabit\", \"servicename\": \"Amazon Elastic Compute Cloud\", \"gpuMemory\": \"NA\", \"dedicatedEbsThroughputDescription\": \"312 Mbps\", \"vpcnetworkingsupport\": \"true\", \"instanceType\": \"m7i-flex.large\", \"tenancy\": \"Shared\", \"usagetype\": \"APS2-BoxUsage:m7i-flex.large\", \"normalizationSizeFactor\": \"4\", \"intelAvxAvailable\": \"Yes\", \"processorFeatures\": \"Intel AVX; Intel AVX2; Intel AVX512; Intel Turbo; Intel AMX\", \"servicecode\": \"AmazonEC2\", \"licenseModel\": \"No License required\", \"currentGeneration\": \"Yes\", \"preInstalledSw\": \"NA\", \"location\": \"Asia Pacific (Sydney)\", \"processorArchitecture\": \"64-bit\", \"marketoption\": \"OnDemand\", \"operation\": \"RunInstances\", \"availabilityzone\": \"NA\"}, \"sku\": \"YZS4YR3ZPHD427K5\"}, \"serviceCode\": \"AmazonEC2\", \"terms\": {\"OnDemand\": {\"YZS4YR3ZPHD427K5.JRTCKXETXF\": {\"priceDimensions\": {\"YZS4YR3ZPHD427K5.JRTCKXETXF.6YS6EN2CT7\": {\"unit\": \"Hrs\", \"endRange\": \"Inf\", \"description\": \"$0.1197 per On Demand Linux m7i-flex.large Instance Hour\", \"appliesTo\": [], \"rateCode\": \"YZS4YR3ZPHD427K5.JRTCKXETXF.6YS6EN2CT7\", \"beginRange\": \"0\", \"pricePerUnit\": {\"USD\": \"0.1197000000\"}}}, \"sku\": \"YZS4YR3ZPHD427K5\", \"effectiveDate\": \"2026-10-01T00:00:00Z\", \"offerTermCode\": \"JRTCKXETXF\", \"termAttributes\": {}}}, \"Reserved\": {\"YZS4YR3ZPHD427K5.CUZHX8X6JH\": {\"priceDimensions\": {\"YZS4YR3ZPHD427K5.CUZHX8X6JH.6YS6EN2CT7\": {\"unit\": \"Hrs\", \"endRange\": \"Inf\", \"description\": \"Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied\", \"appliesTo\": [], \"rateCode\": \"YZS4YR3ZPHD427K5.CUZHX8X6JH.6YS6EN2CT7\", \"beginRange\": \"0\", \"pricePerUnit\": {\"USD\": \"0.0433200000\"}}, \"YZS4YR3ZPHD427K5.CUZHX8X6JH.2TG2D8R56U\": {\"unit\": \"Quantity\", \"description\": \"Upfront Fee\", \"appliesTo\": [], \"rateCode\": \"YZS4YR3ZPHD427K5.CUZHX8X6JH.2TG2D8R56U\", \"pricePerUnit\": {\"USD\": \"380\"}}}, \"sku\": \"YZS4YR3ZPHD427K5\", \"effectiveDate\": \"2026-10-07T17:15:22Z\", \"offerTermCode\": \"CUZHX8X6JH\", \"termAttributes\": {\"LeaseContractLength\": \"1yr\", \"OfferingClass\": \"convertible\", \"PurchaseOption\": \"Partial Upfront\"}}, \"YZS4YR3ZPHD427K5.4NA7Y494T4\": {\"priceDimensions\": {\"YZS4YR3ZPHD427K5.4NA7Y494T4.6YS6EN2CT7\": {\"unit\": \"Hrs\", \"endRange\": \"Inf\", \"description\": \"Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied\", \"appliesTo\": [], \"rateCode\": \"YZS4YR3ZPHD427K5.4NA7Y494T4.6YS6EN2CT7\", \"beginRange\": \"0\", \"pricePerUnit\": {\"USD\": \"0.0791800000\"}}}, \"sku\": \"YZS4YR3ZPHD427K5\", \"effectiveDate\": \"2026-10-07T17:15:25Z\", \"offerTermCode\": \"4NA7Y494T4\", \"termAttributes\": {\"LeaseContractLength\": \"1yr\", \"OfferingClass\": \"standard\", \"PurchaseOption\": \"No Upfront\"}}, \"YZS4YR3ZPHD427K5.38NPMPTW36\": {\"priceDimensions\": {\"YZS4YR3ZPHD427K5.38NPMPTW36.6YS6EN2CT7\": {\"unit\": \"Hrs\", \"endRange\": \"Inf\", \"description\": \"Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied\", \"appliesTo\": [], \"rateCode\": \"YZS4YR3ZPHD427K5.38NPMPTW36.6YS6EN2CT7\", \"beginRange\": \"0\", \"pricePerUnit\": {\"USD\": \"0.0251400000\"}}, \"YZS4YR3ZPHD427K5.38NPMPTW36.2TG2D8R56U\": {\"unit\": \"Quantity\", \"description\": \"Upfront Fee\", \"appliesTo\": [], \"rateCode\": \"YZS4YR3ZPHD427K5.38NPMPTW36.2TG2D8R56U\", \"pricePerUnit\": {\"USD\": \"661\"}}}, \"sku\": \"YZS4YR3ZPHD427K5\", \"effectiveDate\": \"2026-10-07T17:15:21Z\", \"offerTermCode\": \"38NPMPTW36\", \"termAttributes\": {\"LeaseContractLength\": \"3yr\", \"OfferingClass\": \"standard\", \"PurchaseOption\": \"Partial Upfront\"}}, \"YZS4YR3ZPHD427K5.MZU6U2429S\": {\"priceDimensions\": {\"YZS4YR3ZPHD427K5.MZU6U2429S.6YS6EN2CT7\": {\"unit\": \"Hrs\", \"endRange\": \"Inf\", \"description\": \"USD 0.0 per Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied\", \"appliesTo\": [], \"rateCode\": \"YZS4YR3ZPHD427K5.MZU6U2429S.6YS6EN2CT7\", \"beginRange\": \"0\", \"pricePerUnit\": {\"USD\": \"0.0000000000\"}}, \"YZS4YR3ZPHD427K5.MZU6U2429S.2TG2D8R56U\": {\"unit\": \"Quantity\", \"description\": \"Upfront Fee\", \"appliesTo\": [], \"rateCode\": \"YZS4YR3ZPHD427K5.MZU6U2429S.2TG2D8R56U\", \"pricePerUnit\": {\"USD\": \"1494\"}}}, \"sku\": \"YZS4YR3ZPHD427K5\", \"effectiveDate\": \"2026-10-07T17:15:21Z\", \"offerTermCode\": \"MZU6U2429S\", \"termAttributes\": {\"LeaseContractLength\": \"3yr\", \"OfferingClass\": \"convertible\", \"PurchaseOption\": \"All Upfront\"}}, \"YZS4YR3ZPHD427K5.Z2E3P23VKM\": {\"priceDimensions\": {\"YZS4YR3ZPHD427K5.Z2E3P23VKM.6YS6EN2CT7\": {\"unit\": \"Hrs\", \"endRange\": \"Inf\", \"description\": \"Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied\", \"appliesTo\": [], \"rateCode\": \"YZS4YR3ZPHD427K5.Z2E3P23VKM.6YS6EN2CT7\", \"beginRange\": \"0\", \"pricePerUnit\": {\"USD\": \"0.0626700000\"}}}, \"sku\": \"YZS4YR3ZPHD427K5\", \"effectiveDate\": \"2026-10-07T17:15:21Z\", \"offerTermCode\": \"Z2E3P23VKM\", \"termAttributes\": {\"LeaseContractLength\": \"3yr\", \"OfferingClass\": \"convertible\", \"PurchaseOption\": \"No Upfront\"}}, \"YZS4YR3ZPHD427K5.NQ3QZPMQV9\": {\"priceDimensions\": {\"YZS4YR3ZPHD427K5.NQ3QZPMQV9.6YS6EN2CT7\": {\"unit\": \"Hrs\", \"endRange\": \"Inf\", \"description\": \"USD 0.0 per Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied\", \"appliesTo\": [], \"rateCode\": \"YZS4YR3ZPHD427K5.NQ3QZPMQV9.6YS6EN2CT7\", \"beginRange\": \"0\", \"pricePerUnit\": {\"USD\": \"0.0000000000\"}}, \"YZS4YR3ZPHD427K5.NQ3QZPMQV9.2TG2D8R56U\": {\"unit\": \"Quantity\", \"description\": \"Upfront Fee\", \"appliesTo\": [], \"rateCode\": \"YZS4YR3ZPHD427K5.NQ3QZPMQV9.2TG2D8R56U\", \"pricePerUnit\": {\"USD\": \"1242\"}}}, \"sku\": \"YZS4YR3ZPHD427K5\", \"effectiveDate\": \"2026-10-07T17:15:23Z\", \"offerTermCode\": \"NQ3QZPMQV9\", \"termAttributes\": {\"LeaseContractLength\": \"3yr\", \"OfferingClass\": \"standard\", \"PurchaseOption\": \"All Upfront\"}}, \"YZS4YR3ZPHD427K5.HU7G6KETJZ\": {\"priceDimensions\": {\"YZS4YR3ZPHD427K5.HU7G6KETJZ.6YS6EN2CT7\": {\"unit\": \"Hrs\", \"endRange\": \"Inf\", \"description\": \"Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied\", \"appliesTo\": [], \"rateCode\": \"YZS4YR3ZPHD427K5.HU7G6KETJZ.6YS6EN2CT7\", \"beginRange\": \"0\", \"pricePerUnit\": {\"USD\": \"0.0377100000\"}}, \"YZS4YR3ZPHD427K5.HU7G6KETJZ.2TG2D8R56U\": {\"unit\": \"Quantity\", \"description\": \"Upfront Fee\", \"appliesTo\": [], \"rateCode\": \"YZS4YR3ZPHD427K5.HU7G6KETJZ.2TG2D8R56U\", \"pricePerUnit\": {\"USD\": \"330\"}}}, \"sku\": \"YZS4YR3ZPHD427K5\", \"effectiveDate\": \"2026-10-07T17:15:23Z\", \"offerTermCode\": \"HU7G6KETJZ\", \"termAttributes\": {\"LeaseContractLength\": \"1yr\", \"OfferingClass\": \"standard\", \"PurchaseOption\": \"Partial Upfront\"}}, \"YZS4YR3ZPHD427K5.VJWZNREJX2\": {\"priceDimensions\": {\"YZS4YR3ZPHD427K5.VJWZNREJX2.6YS6EN2CT7\": {\"unit\": \"Hrs\", \"endRange\": \"Inf\", \"description\": \"USD 0.0 per Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied\", \"appliesTo\": [], \"rateCode\": \"YZS4YR3ZPHD427K5.VJWZNREJX2.6YS6EN2CT7\", \"beginRange\": \"0\", \"pricePerUnit\": {\"USD\": \"0.0000000000\"}}, \"YZS4YR3ZPHD427K5.VJWZNREJX2.2TG2D8R56U\": {\"unit\": \"Quantity\", \"description\": \"Upfront Fee\", \"appliesTo\": [], \"rateCode\": \"YZS4YR3ZPHD427K5.VJWZNREJX2.2TG2D8R56U\", \"pricePerUnit\": {\"USD\": \"744\"}}}, \"sku\": \"YZS4YR3ZPHD427K5\", \"effectiveDate\": \"2026-10-07T17:15:22Z\", \"offerTermCode\": \"VJWZNREJX2\", \"termAttributes\": {\"LeaseContractLength\": \"1yr\", \"OfferingClass\": \"convertible\", \"PurchaseOption\": \"All Upfront\"}}, \"YZS4YR3ZPHD427K5.6QCMYABX3D\": {\"priceDimensions\": {\"YZS4YR3ZPHD427K5.6QCMYABX3D.6YS6EN2CT7\": {\"unit\": \"Hrs\", \"endRange\": \"Inf\", \"description\": \"USD 0.0 per Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied\", \"appliesTo\": [], \"rateCode\": \"YZS4YR3ZPHD427K5.6QCMYABX3D.6YS6EN2CT7\", \"beginRange\": \"0\", \"pricePerUnit\": {\"USD\": \"0.0000000000\"}}, \"YZS4YR3ZPHD427K5.6QCMYABX3D.2TG2D8R56U\": {\"unit\": \"Quantity\", \"description\": \"Upfront Fee\", \"appliesTo\": [], \"rateCode\": \"YZS4YR3ZPHD427K5.6QCMYABX3D.2TG2D8R56U\", \"pricePerUnit\": {\"USD\": \"647\"}}}, \"sku\": \"YZS4YR3ZPHD427K5\", \"effectiveDate\": \"2026-10-07T17:15:23Z\", \"offerTermCode\": \"6QCMYABX3D\", \"termAttributes\": {\"LeaseContractLength\": \"1yr\", \"OfferingClass\": \"standard\", \"PurchaseOption\": \"All Upfront\"}}, \"YZS4YR3ZPHD427K5.BPH4J8HBKS\": {\"priceDimensions\": {\"YZS4YR3ZPHD427K5.BPH4J8HBKS.6YS6EN2CT7\": {\"unit\": \"Hrs\", \"endRange\": \"Inf\", \"description\": \"Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied\", \"appliesTo\": [], \"rateCode\": \"YZS4YR3ZPHD427K5.BPH4J8HBKS.6YS6EN2CT7\", \"beginRange\": \"0\", \"pricePerUnit\": {\"USD\": \"0.0543000000\"}}}, \"sku\": \"YZS4YR3ZPHD427K5\", \"effectiveDate\": \"2026-10-07T17:15:21Z\", \"offerTermCode\": \"BPH4J8HBKS\", \"termAttributes\": {\"LeaseContractLength\": \"3yr\", \"OfferingClass\": \"standard\", \"PurchaseOption\": \"No Upfront\"}}, \"YZS4YR3ZPHD427K5.R5XV2EPZQZ\": {\"priceDimensions\": {\"YZS4YR3ZPHD427K5.R5XV2EPZQZ.2TG2D8R56U\": {\"unit\": \"Quantity\", \"description\": \"Upfront Fee\", \"appliesTo\": [], \"rateCode\": \"YZS4YR3ZPHD427K5.R5XV2EPZQZ.2TG2D8R56U\", \"pricePerUnit\": {\"USD\": \"762\"}}, \"YZS4YR3ZPHD427K5.R5XV2EPZQZ.6YS6EN2CT7\": {\"unit\": \"Hrs\", \"endRange\": \"Inf\", \"description\": \"Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied\", \"appliesTo\": [], \"rateCode\": \"YZS4YR3ZPHD427K5.R5XV2EPZQZ.6YS6EN2CT7\", \"beginRange\": \"0\", \"pricePerUnit\": {\"USD\": \"0.0290100000\"}}}, \"sku\": \"YZS4YR3ZPHD427K5\", \"effectiveDate\": \"2026-10-07T17:15:21Z\", \"offerTermCode\": \"R5XV2EPZQZ\", \"termAttributes\": {\"LeaseContractLength\": \"3yr\", \"OfferingClass\": \"convertible\", \"PurchaseOption\": \"Partial Upfront\"}}, \"YZS4YR3ZPHD427K5.7NE97W5U4E\": {\"priceDimensions\": {\"YZS4YR3ZPHD427K5.7NE97W5U4E.6YS6EN2CT7\": {\"unit\": \"Hrs\", \"endRange\": \"Inf\", \"description\": \"Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied\", \"appliesTo\": [], \"rateCode\": \"YZS4YR3ZPHD427K5.7NE97W5U4E.6YS6EN2CT7\", \"beginRange\": \"0\", \"pricePerUnit\": {\"USD\": \"0.0909800000\"}}}, \"sku\": \"YZS4YR3ZPHD427K5\", \"effectiveDate\": \"2026-10-07T17:15:22Z\", \"offerTermCode\": \"7NE97W5U4E\", \"termAttributes\": {\"LeaseContractLength\": \"1yr\", \"OfferingClass\": \"convertible\", \"PurchaseOption\": \"No Upfront\"}}}}, \"version\": \"20261007165408\", \"publicationDate\": \"2026-10-07T16:54:08Z\"}]}, \"price_disk\": {\"products\": [{\"product\": {\"productFamily\": \"Storage\", \"attributes\": {\"maxThroughputvolume\": \"2000 MiB/s\", \"volumeType\": \"General Purpose\", \"maxIopsvolume\": \"80000\", \"usagetype\": \"APS2-EBS:VolumeUsage.gp3\", \"locationType\": \"AWS Region\", \"maxVolumeSize\": \"64 TiB\", \"storageMedia\": \"SSD-backed\", \"regionCode\": \"ap-southeast-2\", \"servicecode\": \"AmazonEC2\", \"volumeApiName\": \"gp3\", \"location\": \"Asia Pacific (Sydney)\", \"servicename\": \"Amazon Elastic Compute Cloud\", \"operation\": \"\"}, \"sku\": \"QR74UAP3E9WUYT9B\"}, \"serviceCode\": \"AmazonEC2\", \"terms\": {\"OnDemand\": {\"QR74UAP3E9WUYT9B.JRTCKXETXF\": {\"priceDimensions\": {\"QR74UAP3E9WUYT9B.JRTCKXETXF.6YS6EN2CT7\": {\"unit\": \"GB-Mo\", \"endRange\": \"Inf\", \"description\": \"$0.096 per GB-month of General Purpose (gp3) provisioned storage - Asia Pacific (Sydney)\", \"appliesTo\": [], \"rateCode\": \"QR74UAP3E9WUYT9B.JRTCKXETXF.6YS6EN2CT7\", \"beginRange\": \"0\", \"pricePerUnit\": {\"USD\": \"0.0960000000\"}}}, \"sku\": \"QR74UAP3E9WUYT9B\", \"effectiveDate\": \"2026-10-01T00:00:00Z\", \"offerTermCode\": \"JRTCKXETXF\", \"termAttributes\": {}}}}, \"version\": \"20261007165408\", \"publicationDate\": \"2026-10-07T16:54:08Z\"}]}, \"price_ipv4\": {\"products\": [{\"product\": {\"attributes\": {\"regionCode\": \"ap-southeast-2\", \"servicecode\": \"AmazonVPC\", \"groupDescription\": \"Hourly charge for In-use Public IPv4 Addresses\", \"usagetype\": \"APS2-PublicIPv4:InUseAddress\", \"locationType\": \"AWS Region\", \"location\": \"Asia Pacific (Sydney)\", \"servicename\": \"Amazon Virtual Private Cloud\", \"operation\": \"\", \"group\": \"VPCPublicIPv4Address\"}, \"sku\": \"JZP2PURP9VVQ96GH\"}, \"serviceCode\": \"AmazonVPC\", \"terms\": {\"OnDemand\": {\"JZP2PURP9VVQ96GH.JRTCKXETXF\": {\"priceDimensions\": {\"JZP2PURP9VVQ96GH.JRTCKXETXF.6YS6EN2CT7\": {\"unit\": \"Hrs\", \"endRange\": \"Inf\", \"description\": \"$0.005 per In-use public IPv4 address per hour\", \"appliesTo\": [], \"rateCode\": \"JZP2PURP9VVQ96GH.JRTCKXETXF.6YS6EN2CT7\", \"beginRange\": \"0\", \"pricePerUnit\": {\"USD\": \"0.0050000000\"}}}, \"sku\": \"JZP2PURP9VVQ96GH\", \"effectiveDate\": \"2026-09-01T00:00:00Z\", \"offerTermCode\": \"JRTCKXETXF\", \"termAttributes\": {}}}}, \"version\": \"20260917190528\", \"publicationDate\": \"2026-09-17T19:05:28Z\"}]}, \"price_s3\": {\"products\": [{\"product\": {\"productFamily\": \"Storage\", \"attributes\": {\"volumeType\": \"Standard\", \"storageClass\": \"General Purpose\", \"regionCode\": \"ap-southeast-2\", \"servicecode\": \"AmazonS3\", \"durability\": \"99.999999999%\", \"usagetype\": \"APS2-TimedStorage-ByteHrs\", \"locationType\": \"AWS Region\", \"location\": \"Asia Pacific (Sydney)\", \"servicename\": \"Amazon Simple Storage Service\", \"availability\": \"99.99%\", \"operation\": \"\"}, \"sku\": \"5QVJMK36NJC9G6DC\"}, \"serviceCode\": \"AmazonS3\", \"terms\": {\"OnDemand\": {\"5QVJMK36NJC9G6DC.JRTCKXETXF\": {\"priceDimensions\": {\"5QVJMK36NJC9G6DC.JRTCKXETXF.PGHJ3S3EYE\": {\"unit\": \"GB-Mo\", \"endRange\": \"51200\", \"description\": \"$0.025 per GB - first 50 TB / month of storage used\", \"appliesTo\": [], \"rateCode\": \"5QVJMK36NJC9G6DC.JRTCKXETXF.PGHJ3S3EYE\", \"beginRange\": \"0\", \"pricePerUnit\": {\"USD\": \"0.0250000000\"}}, \"5QVJMK36NJC9G6DC.JRTCKXETXF.D42MF2PVJS\": {\"unit\": \"GB-Mo\", \"endRange\": \"512000\", \"description\": \"$0.024 per GB - next 450 TB / month of storage used\", \"appliesTo\": [], \"rateCode\": \"5QVJMK36NJC9G6DC.JRTCKXETXF.D42MF2PVJS\", \"beginRange\": \"51200\", \"pricePerUnit\": {\"USD\": \"0.0240000000\"}}, \"5QVJMK36NJC9G6DC.JRTCKXETXF.PXJDJ3YRG3\": {\"unit\": \"GB-Mo\", \"endRange\": \"Inf\", \"description\": \"$0.023 per GB - storage used / month over 500 TB\", \"appliesTo\": [], \"rateCode\": \"5QVJMK36NJC9G6DC.JRTCKXETXF.PXJDJ3YRG3\", \"beginRange\": \"512000\", \"pricePerUnit\": {\"USD\": \"0.0230000000\"}}}, \"sku\": \"5QVJMK36NJC9G6DC\", \"effectiveDate\": \"2026-09-01T00:00:00Z\", \"offerTermCode\": \"JRTCKXETXF\", \"termAttributes\": {}}}}, \"version\": \"20260928230416\", \"publicationDate\": \"2026-09-28T23:04:16Z\"}]}}, \"warning\": null, \"api_calls\": [{\"service\": \"freetier\", \"operation\": \"GetAccountPlanState\", \"status\": \"success\"}, {\"service\": \"ec2\", \"operation\": \"DescribeInstances\", \"status\": \"success\", \"n_items\": {\"Reservations\": 1}}, {\"service\": \"ec2\", \"operation\": \"DescribeVolumes\", \"status\": \"success\", \"n_items\": {\"Volumes\": 1}}, {\"service\": \"ec2\", \"operation\": \"DescribeImages\", \"status\": \"success\", \"n_items\": {\"Images\": 1}}, {\"service\": \"ec2\", \"operation\": \"DescribeSubnets\", \"status\": \"success\", \"n_items\": {\"Subnets\": 1}}, {\"service\": \"ec2\", \"operation\": \"DescribeSecurityGroups\", \"status\": \"success\", \"n_items\": {\"SecurityGroups\": 1}}, {\"service\": \"ec2\", \"operation\": \"DescribeRouteTables\", \"status\": \"success\", \"n_items\": {\"RouteTables\": 1}}, {\"service\": \"iam\", \"operation\": \"GetInstanceProfile\", \"status\": \"success\"}, {\"service\": \"s3\", \"operation\": \"GetBucketVersioning\", \"status\": \"success\"}, {\"service\": \"pricing\", \"operation\": \"GetProducts\", \"status\": \"success\", \"n_items\": {\"PriceList\": 1}}, {\"service\": \"pricing\", \"operation\": \"GetProducts\", \"status\": \"success\", \"n_items\": {\"PriceList\": 1}}, {\"service\": \"pricing\", \"operation\": \"GetProducts\", \"status\": \"success\", \"n_items\": {\"PriceList\": 1}}, {\"service\": \"pricing\", \"operation\": \"GetProducts\", \"status\": \"success\", \"n_items\": {\"PriceList\": 1}}]}"
        }
      ],
      "structuredContent": {
        "status": "success",
        "stdout": "",
        "return_value": {
          "credits": {
            "accountId": "803656589923",
            "accountPlanType": "FREE",
            "accountPlanStatus": "ACTIVE",
            "accountPlanRemainingCredits": {
              "amount": 119.37,
              "unit": "USD"
            },
            "accountPlanExpirationDate": "2027-04-05T13:45:14.308000+00:00"
          },
          "old_host": {
            "Reservations": [
              {
                "ReservationId": "r-09dd2a8d6fada358a",
                "OwnerId": "803656589923",
                "Groups": [],
                "Instances": [
                  {
                    "Architecture": "x86_64",
                    "BlockDeviceMappings": [
                      {
                        "DeviceName": "/dev/sda1",
                        "Ebs": {
                          "AttachTime": "2026-10-07T15:29:06+00:00",
                          "DeleteOnTermination": false,
                          "Status": "attached",
                          "VolumeId": "vol-07baf9132bce08e77",
                          "EbsCardIndex": 0
                        }
                      }
                    ],
                    "ClientToken": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9",
                    "EbsOptimized": false,
                    "EnaSupport": true,
                    "Hypervisor": "xen",
                    "IamInstanceProfile": {
                      "Arn": "arn:aws:iam::803656589923:instance-profile/FYP-p85-01a116f7-3b82-7a79-8653-3aee62dc99e9",
                      "Id": "AIPA3WHNKMJRVRF7W6G3I"
                    },
                    "NetworkInterfaces": [
                      {
                        "Attachment": {
                          "AttachTime": "2026-10-07T15:29:05+00:00",
                          "AttachmentId": "eni-attach-0813fcecf35d7cf54",
                          "DeleteOnTermination": true,
                          "DeviceIndex": 0,
                          "Status": "attached",
                          "NetworkCardIndex": 0
                        },
                        "Description": "",
                        "Groups": [
                          {
                            "GroupId": "sg-076d87ac5db0a6f52",
                            "GroupName": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                          }
                        ],
                        "Ipv6Addresses": [],
                        "MacAddress": "02:ff:c8:a3:48:07",
                        "NetworkInterfaceId": "eni-0b2d2e6ce97e47a2f",
                        "OwnerId": "803656589923",
                        "PrivateDnsName": "ip-172-31-4-109.ap-southeast-2.compute.internal",
                        "PrivateIpAddress": "172.31.4.109",
                        "PrivateIpAddresses": [
                          {
                            "Primary": true,
                            "PrivateDnsName": "ip-172-31-4-109.ap-southeast-2.compute.internal",
                            "PrivateIpAddress": "172.31.4.109"
                          }
                        ],
                        "SourceDestCheck": true,
                        "Status": "in-use",
                        "SubnetId": "subnet-05c5c729c83dc651b",
                        "VpcId": "vpc-0c74e59331cbc1caa",
                        "InterfaceType": "interface",
                        "Operator": {
                          "Managed": false
                        }
                      }
                    ],
                    "RootDeviceName": "/dev/sda1",
                    "RootDeviceType": "ebs",
                    "SecurityGroups": [
                      {
                        "GroupId": "sg-076d87ac5db0a6f52",
                        "GroupName": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                      }
                    ],
                    "SourceDestCheck": true,
                    "StateReason": {
                      "Code": "Client.UserInitiatedShutdown",
                      "Message": "Client.UserInitiatedShutdown: User initiated shutdown"
                    },
                    "Tags": [
                      {
                        "Key": "research.owner",
                        "Value": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                      },
                      {
                        "Key": "Name",
                        "Value": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                      },
                      {
                        "Key": "research.stage",
                        "Value": "8.5"
                      }
                    ],
                    "VirtualizationType": "hvm",
                    "CpuOptions": {
                      "CoreCount": 1,
                      "ThreadsPerCore": 2
                    },
                    "CapacityReservationSpecification": {
                      "CapacityReservationPreference": "open"
                    },
                    "HibernationOptions": {
                      "Configured": false
                    },
                    "MetadataOptions": {
                      "State": "applied",
                      "HttpTokens": "required",
                      "HttpPutResponseHopLimit": 1,
                      "HttpEndpoint": "enabled",
                      "HttpProtocolIpv6": "disabled",
                      "InstanceMetadataTags": "disabled"
                    },
                    "EnclaveOptions": {
                      "Enabled": false
                    },
                    "BootMode": "uefi-preferred",
                    "PlatformDetails": "Linux/UNIX",
                    "UsageOperation": "RunInstances",
                    "UsageOperationUpdateTime": "2026-10-07T15:29:05+00:00",
                    "PrivateDnsNameOptions": {
                      "HostnameType": "ip-name",
                      "EnableResourceNameDnsARecord": false,
                      "EnableResourceNameDnsAAAARecord": false
                    },
                    "MaintenanceOptions": {
                      "AutoRecovery": "default",
                      "RebootMigration": "default"
                    },
                    "CurrentInstanceBootMode": "uefi",
                    "NetworkPerformanceOptions": {
                      "BandwidthWeighting": "default"
                    },
                    "Operator": {
                      "Managed": false,
                      "HiddenByDefault": false
                    },
                    "InstanceId": "i-0a6196aff6f8098ac",
                    "ImageId": "ami-090b1140798d2d006",
                    "State": {
                      "Code": 80,
                      "Name": "stopped"
                    },
                    "PrivateDnsName": "ip-172-31-4-109.ap-southeast-2.compute.internal",
                    "PublicDnsName": "",
                    "StateTransitionReason": "User initiated (2026-10-07 15:57:46 GMT)",
                    "AmiLaunchIndex": 0,
                    "ProductCodes": [],
                    "InstanceType": "m7i-flex.large",
                    "LaunchTime": "2026-10-07T15:29:05+00:00",
                    "Placement": {
                      "AvailabilityZoneId": "apse2-az1",
                      "GroupName": "",
                      "Tenancy": "default",
                      "AvailabilityZone": "ap-southeast-2a"
                    },
                    "Monitoring": {
                      "State": "disabled"
                    },
                    "SubnetId": "subnet-05c5c729c83dc651b",
                    "VpcId": "vpc-0c74e59331cbc1caa",
                    "PrivateIpAddress": "172.31.4.109"
                  }
                ]
              }
            ]
          },
          "old_disk": {
            "Volumes": [
              {
                "AvailabilityZoneId": "apse2-az1",
                "Iops": 3000,
                "Tags": [
                  {
                    "Key": "Name",
                    "Value": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                  },
                  {
                    "Key": "research.owner",
                    "Value": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                  },
                  {
                    "Key": "research.stage",
                    "Value": "8.5"
                  }
                ],
                "VolumeType": "gp3",
                "MultiAttachEnabled": false,
                "Throughput": 125,
                "Operator": {
                  "Managed": false,
                  "HiddenByDefault": false
                },
                "VolumeArn": "arn:aws:ec2:ap-southeast-2:803656589923:volume/vol-07baf9132bce08e77",
                "OwnerId": "803656589923",
                "VolumeId": "vol-07baf9132bce08e77",
                "Size": 160,
                "SnapshotId": "snap-04f8536d791ceaecf",
                "AvailabilityZone": "ap-southeast-2a",
                "State": "in-use",
                "CreateTime": "2026-10-07T15:29:06.157000+00:00",
                "Attachments": [
                  {
                    "DeleteOnTermination": false,
                    "EbsCardIndex": 0,
                    "VolumeId": "vol-07baf9132bce08e77",
                    "InstanceId": "i-0a6196aff6f8098ac",
                    "Device": "/dev/sda1",
                    "State": "attached",
                    "AttachTime": "2026-10-07T15:29:06+00:00"
                  }
                ],
                "Encrypted": true,
                "KmsKeyId": "arn:aws:kms:ap-southeast-2:803656589923:key/1ad9e0e5-ad7c-4f52-8b41-50c266898626"
              }
            ]
          },
          "image": {
            "Images": [
              {
                "PlatformDetails": "Linux/UNIX",
                "UsageOperation": "RunInstances",
                "BlockDeviceMappings": [
                  {
                    "Ebs": {
                      "DeleteOnTermination": true,
                      "SnapshotId": "snap-04f8536d791ceaecf",
                      "VolumeSize": 8,
                      "VolumeType": "gp3",
                      "Encrypted": false
                    },
                    "DeviceName": "/dev/sda1"
                  },
                  {
                    "DeviceName": "/dev/sdb",
                    "VirtualName": "ephemeral0"
                  },
                  {
                    "DeviceName": "/dev/sdc",
                    "VirtualName": "ephemeral1"
                  }
                ],
                "Description": "Canonical, Ubuntu, 24.04, amd64 noble image",
                "EnaSupport": true,
                "Hypervisor": "xen",
                "ImageOwnerAlias": "amazon",
                "Name": "ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-20260923",
                "RootDeviceName": "/dev/sda1",
                "RootDeviceType": "ebs",
                "SriovNetSupport": "simple",
                "VirtualizationType": "hvm",
                "BootMode": "uefi-preferred",
                "DeprecationTime": "2028-09-23T11:57:18.000Z",
                "ImdsSupport": "v2.0",
                "FreeTierEligible": true,
                "PublicSsmParameterName": "aws/service/canonical/ubuntu/server/noble/stable/current/amd64/hvm/ebs-gp3/ami-id",
                "ImageId": "ami-090b1140798d2d006",
                "ImageLocation": "amazon/ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-20260923",
                "State": "available",
                "OwnerId": "099720109477",
                "CreationDate": "2026-09-23T11:57:18.000Z",
                "Public": true,
                "Architecture": "x86_64",
                "ImageType": "machine"
              }
            ]
          },
          "subnet": {
            "Subnets": [
              {
                "AvailabilityZoneId": "apse2-az1",
                "MapCustomerOwnedIpOnLaunch": false,
                "OwnerId": "803656589923",
                "AssignIpv6AddressOnCreation": false,
                "Ipv6CidrBlockAssociationSet": [],
                "SubnetArn": "arn:aws:ec2:ap-southeast-2:803656589923:subnet/subnet-05c5c729c83dc651b",
                "EnableDns64": false,
                "Ipv6Native": false,
                "PrivateDnsNameOptionsOnLaunch": {
                  "HostnameType": "ip-name",
                  "EnableResourceNameDnsARecord": false,
                  "EnableResourceNameDnsAAAARecord": false
                },
                "BlockPublicAccessStates": {
                  "InternetGatewayBlockMode": "off"
                },
                "SubnetId": "subnet-05c5c729c83dc651b",
                "State": "available",
                "VpcId": "vpc-0c74e59331cbc1caa",
                "CidrBlock": "172.31.0.0/20",
                "AvailableIpAddressCount": 4090,
                "AvailabilityZone": "ap-southeast-2a",
                "DefaultForAz": true,
                "MapPublicIpOnLaunch": true
              }
            ]
          },
          "security": {
            "SecurityGroups": [
              {
                "GroupId": "sg-076d87ac5db0a6f52",
                "IpPermissionsEgress": [
                  {
                    "IpProtocol": "-1",
                    "UserIdGroupPairs": [],
                    "IpRanges": [
                      {
                        "CidrIp": "0.0.0.0/0"
                      }
                    ],
                    "Ipv6Ranges": [],
                    "PrefixListIds": []
                  }
                ],
                "Tags": [
                  {
                    "Key": "research.owner",
                    "Value": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                  },
                  {
                    "Key": "Name",
                    "Value": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                  },
                  {
                    "Key": "research.stage",
                    "Value": "8.5"
                  }
                ],
                "VpcId": "vpc-0c74e59331cbc1caa",
                "SecurityGroupArn": "arn:aws:ec2:ap-southeast-2:803656589923:security-group/sg-076d87ac5db0a6f52",
                "OwnerId": "803656589923",
                "GroupName": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9",
                "Description": "Frozen Phase 8 serial research: SSM only, no inbound ports",
                "IpPermissions": []
              }
            ]
          },
          "routes": {
            "RouteTables": [
              {
                "Associations": [
                  {
                    "Main": true,
                    "RouteTableAssociationId": "rtbassoc-0c98c36c2eac50733",
                    "RouteTableId": "rtb-06ba3e3d927d5aea6",
                    "AssociationState": {
                      "State": "associated"
                    }
                  }
                ],
                "PropagatingVgws": [],
                "RouteTableId": "rtb-06ba3e3d927d5aea6",
                "Routes": [
                  {
                    "DestinationCidrBlock": "172.31.0.0/16",
                    "GatewayId": "local",
                    "Origin": "CreateRouteTable",
                    "State": "active"
                  },
                  {
                    "DestinationCidrBlock": "0.0.0.0/0",
                    "GatewayId": "igw-05c25cbe2b04b9b01",
                    "Origin": "CreateRoute",
                    "State": "active"
                  }
                ],
                "Tags": [],
                "VpcId": "vpc-0c74e59331cbc1caa",
                "OwnerId": "803656589923"
              }
            ]
          },
          "profile": {
            "InstanceProfile": {
              "Path": "/",
              "InstanceProfileName": "FYP-p85-01a116f7-3b82-7a79-8653-3aee62dc99e9",
              "InstanceProfileId": "AIPA3WHNKMJRVRF7W6G3I",
              "Arn": "arn:aws:iam::803656589923:instance-profile/FYP-p85-01a116f7-3b82-7a79-8653-3aee62dc99e9",
              "CreateDate": "2026-10-07T15:25:44+00:00",
              "Roles": [
                {
                  "Path": "/",
                  "RoleName": "FYP-p85-01a116f7-3b82-7a79-8653-3aee62dc99e9",
                  "RoleId": "AROA3WHNKMJR4XAOKYDGF",
                  "Arn": "arn:aws:iam::803656589923:role/FYP-p85-01a116f7-3b82-7a79-8653-3aee62dc99e9",
                  "CreateDate": "2026-10-07T15:25:43+00:00",
                  "AssumeRolePolicyDocument": {
                    "Version": "2012-10-17",
                    "Statement": [
                      {
                        "Effect": "Allow",
                        "Principal": {
                          "Service": "ec2.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                      }
                    ]
                  }
                }
              ],
              "Tags": [
                {
                  "Key": "research.owner",
                  "Value": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                },
                {
                  "Key": "research.stage",
                  "Value": "8.5"
                },
                {
                  "Key": "Name",
                  "Value": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                }
              ]
            }
          },
          "versioning": {
            "Status": "Enabled"
          },
          "price_compute": {
            "products": [
              {
                "product": {
                  "productFamily": "Compute Instance",
                  "attributes": {
                    "enhancedNetworkingSupported": "Yes",
                    "intelTurboAvailable": "Yes",
                    "memory": "8 GiB",
                    "dedicatedEbsThroughput": "Up to 10000 Mbps",
                    "vcpu": "2",
                    "classicnetworkingsupport": "false",
                    "capacitystatus": "Used",
                    "locationType": "AWS Region",
                    "storage": "EBS only",
                    "instanceFamily": "General purpose",
                    "operatingSystem": "Linux",
                    "intelAvx2Available": "Yes",
                    "instanceFamilyCategory": "General Purpose",
                    "regionCode": "ap-southeast-2",
                    "physicalProcessor": "Intel Xeon Scalable (Sapphire Rapids)",
                    "clockSpeed": "3.5 GHz",
                    "ecu": "NA",
                    "networkPerformance": "Up to 12500 Megabit",
                    "servicename": "Amazon Elastic Compute Cloud",
                    "gpuMemory": "NA",
                    "dedicatedEbsThroughputDescription": "312 Mbps",
                    "vpcnetworkingsupport": "true",
                    "instanceType": "m7i-flex.large",
                    "tenancy": "Shared",
                    "usagetype": "APS2-BoxUsage:m7i-flex.large",
                    "normalizationSizeFactor": "4",
                    "intelAvxAvailable": "Yes",
                    "processorFeatures": "Intel AVX; Intel AVX2; Intel AVX512; Intel Turbo; Intel AMX",
                    "servicecode": "AmazonEC2",
                    "licenseModel": "No License required",
                    "currentGeneration": "Yes",
                    "preInstalledSw": "NA",
                    "location": "Asia Pacific (Sydney)",
                    "processorArchitecture": "64-bit",
                    "marketoption": "OnDemand",
                    "operation": "RunInstances",
                    "availabilityzone": "NA"
                  },
                  "sku": "YZS4YR3ZPHD427K5"
                },
                "serviceCode": "AmazonEC2",
                "terms": {
                  "OnDemand": {
                    "YZS4YR3ZPHD427K5.JRTCKXETXF": {
                      "priceDimensions": {
                        "YZS4YR3ZPHD427K5.JRTCKXETXF.6YS6EN2CT7": {
                          "unit": "Hrs",
                          "endRange": "Inf",
                          "description": "$0.1197 per On Demand Linux m7i-flex.large Instance Hour",
                          "appliesTo": [],
                          "rateCode": "YZS4YR3ZPHD427K5.JRTCKXETXF.6YS6EN2CT7",
                          "beginRange": "0",
                          "pricePerUnit": {
                            "USD": "0.1197000000"
                          }
                        }
                      },
                      "sku": "YZS4YR3ZPHD427K5",
                      "effectiveDate": "2026-10-01T00:00:00Z",
                      "offerTermCode": "JRTCKXETXF",
                      "termAttributes": {}
                    }
                  },
                  "Reserved": {
                    "YZS4YR3ZPHD427K5.CUZHX8X6JH": {
                      "priceDimensions": {
                        "YZS4YR3ZPHD427K5.CUZHX8X6JH.6YS6EN2CT7": {
                          "unit": "Hrs",
                          "endRange": "Inf",
                          "description": "Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied",
                          "appliesTo": [],
                          "rateCode": "YZS4YR3ZPHD427K5.CUZHX8X6JH.6YS6EN2CT7",
                          "beginRange": "0",
                          "pricePerUnit": {
                            "USD": "0.0433200000"
                          }
                        },
                        "YZS4YR3ZPHD427K5.CUZHX8X6JH.2TG2D8R56U": {
                          "unit": "Quantity",
                          "description": "Upfront Fee",
                          "appliesTo": [],
                          "rateCode": "YZS4YR3ZPHD427K5.CUZHX8X6JH.2TG2D8R56U",
                          "pricePerUnit": {
                            "USD": "380"
                          }
                        }
                      },
                      "sku": "YZS4YR3ZPHD427K5",
                      "effectiveDate": "2026-10-07T17:15:22Z",
                      "offerTermCode": "CUZHX8X6JH",
                      "termAttributes": {
                        "LeaseContractLength": "1yr",
                        "OfferingClass": "convertible",
                        "PurchaseOption": "Partial Upfront"
                      }
                    },
                    "YZS4YR3ZPHD427K5.4NA7Y494T4": {
                      "priceDimensions": {
                        "YZS4YR3ZPHD427K5.4NA7Y494T4.6YS6EN2CT7": {
                          "unit": "Hrs",
                          "endRange": "Inf",
                          "description": "Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied",
                          "appliesTo": [],
                          "rateCode": "YZS4YR3ZPHD427K5.4NA7Y494T4.6YS6EN2CT7",
                          "beginRange": "0",
                          "pricePerUnit": {
                            "USD": "0.0791800000"
                          }
                        }
                      },
                      "sku": "YZS4YR3ZPHD427K5",
                      "effectiveDate": "2026-10-07T17:15:25Z",
                      "offerTermCode": "4NA7Y494T4",
                      "termAttributes": {
                        "LeaseContractLength": "1yr",
                        "OfferingClass": "standard",
                        "PurchaseOption": "No Upfront"
                      }
                    },
                    "YZS4YR3ZPHD427K5.38NPMPTW36": {
                      "priceDimensions": {
                        "YZS4YR3ZPHD427K5.38NPMPTW36.6YS6EN2CT7": {
                          "unit": "Hrs",
                          "endRange": "Inf",
                          "description": "Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied",
                          "appliesTo": [],
                          "rateCode": "YZS4YR3ZPHD427K5.38NPMPTW36.6YS6EN2CT7",
                          "beginRange": "0",
                          "pricePerUnit": {
                            "USD": "0.0251400000"
                          }
                        },
                        "YZS4YR3ZPHD427K5.38NPMPTW36.2TG2D8R56U": {
                          "unit": "Quantity",
                          "description": "Upfront Fee",
                          "appliesTo": [],
                          "rateCode": "YZS4YR3ZPHD427K5.38NPMPTW36.2TG2D8R56U",
                          "pricePerUnit": {
                            "USD": "661"
                          }
                        }
                      },
                      "sku": "YZS4YR3ZPHD427K5",
                      "effectiveDate": "2026-10-07T17:15:21Z",
                      "offerTermCode": "38NPMPTW36",
                      "termAttributes": {
                        "LeaseContractLength": "3yr",
                        "OfferingClass": "standard",
                        "PurchaseOption": "Partial Upfront"
                      }
                    },
                    "YZS4YR3ZPHD427K5.MZU6U2429S": {
                      "priceDimensions": {
                        "YZS4YR3ZPHD427K5.MZU6U2429S.6YS6EN2CT7": {
                          "unit": "Hrs",
                          "endRange": "Inf",
                          "description": "USD 0.0 per Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied",
                          "appliesTo": [],
                          "rateCode": "YZS4YR3ZPHD427K5.MZU6U2429S.6YS6EN2CT7",
                          "beginRange": "0",
                          "pricePerUnit": {
                            "USD": "0.0000000000"
                          }
                        },
                        "YZS4YR3ZPHD427K5.MZU6U2429S.2TG2D8R56U": {
                          "unit": "Quantity",
                          "description": "Upfront Fee",
                          "appliesTo": [],
                          "rateCode": "YZS4YR3ZPHD427K5.MZU6U2429S.2TG2D8R56U",
                          "pricePerUnit": {
                            "USD": "1494"
                          }
                        }
                      },
                      "sku": "YZS4YR3ZPHD427K5",
                      "effectiveDate": "2026-10-07T17:15:21Z",
                      "offerTermCode": "MZU6U2429S",
                      "termAttributes": {
                        "LeaseContractLength": "3yr",
                        "OfferingClass": "convertible",
                        "PurchaseOption": "All Upfront"
                      }
                    },
                    "YZS4YR3ZPHD427K5.Z2E3P23VKM": {
                      "priceDimensions": {
                        "YZS4YR3ZPHD427K5.Z2E3P23VKM.6YS6EN2CT7": {
                          "unit": "Hrs",
                          "endRange": "Inf",
                          "description": "Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied",
                          "appliesTo": [],
                          "rateCode": "YZS4YR3ZPHD427K5.Z2E3P23VKM.6YS6EN2CT7",
                          "beginRange": "0",
                          "pricePerUnit": {
                            "USD": "0.0626700000"
                          }
                        }
                      },
                      "sku": "YZS4YR3ZPHD427K5",
                      "effectiveDate": "2026-10-07T17:15:21Z",
                      "offerTermCode": "Z2E3P23VKM",
                      "termAttributes": {
                        "LeaseContractLength": "3yr",
                        "OfferingClass": "convertible",
                        "PurchaseOption": "No Upfront"
                      }
                    },
                    "YZS4YR3ZPHD427K5.NQ3QZPMQV9": {
                      "priceDimensions": {
                        "YZS4YR3ZPHD427K5.NQ3QZPMQV9.6YS6EN2CT7": {
                          "unit": "Hrs",
                          "endRange": "Inf",
                          "description": "USD 0.0 per Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied",
                          "appliesTo": [],
                          "rateCode": "YZS4YR3ZPHD427K5.NQ3QZPMQV9.6YS6EN2CT7",
                          "beginRange": "0",
                          "pricePerUnit": {
                            "USD": "0.0000000000"
                          }
                        },
                        "YZS4YR3ZPHD427K5.NQ3QZPMQV9.2TG2D8R56U": {
                          "unit": "Quantity",
                          "description": "Upfront Fee",
                          "appliesTo": [],
                          "rateCode": "YZS4YR3ZPHD427K5.NQ3QZPMQV9.2TG2D8R56U",
                          "pricePerUnit": {
                            "USD": "1242"
                          }
                        }
                      },
                      "sku": "YZS4YR3ZPHD427K5",
                      "effectiveDate": "2026-10-07T17:15:23Z",
                      "offerTermCode": "NQ3QZPMQV9",
                      "termAttributes": {
                        "LeaseContractLength": "3yr",
                        "OfferingClass": "standard",
                        "PurchaseOption": "All Upfront"
                      }
                    },
                    "YZS4YR3ZPHD427K5.HU7G6KETJZ": {
                      "priceDimensions": {
                        "YZS4YR3ZPHD427K5.HU7G6KETJZ.6YS6EN2CT7": {
                          "unit": "Hrs",
                          "endRange": "Inf",
                          "description": "Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied",
                          "appliesTo": [],
                          "rateCode": "YZS4YR3ZPHD427K5.HU7G6KETJZ.6YS6EN2CT7",
                          "beginRange": "0",
                          "pricePerUnit": {
                            "USD": "0.0377100000"
                          }
                        },
                        "YZS4YR3ZPHD427K5.HU7G6KETJZ.2TG2D8R56U": {
                          "unit": "Quantity",
                          "description": "Upfront Fee",
                          "appliesTo": [],
                          "rateCode": "YZS4YR3ZPHD427K5.HU7G6KETJZ.2TG2D8R56U",
                          "pricePerUnit": {
                            "USD": "330"
                          }
                        }
                      },
                      "sku": "YZS4YR3ZPHD427K5",
                      "effectiveDate": "2026-10-07T17:15:23Z",
                      "offerTermCode": "HU7G6KETJZ",
                      "termAttributes": {
                        "LeaseContractLength": "1yr",
                        "OfferingClass": "standard",
                        "PurchaseOption": "Partial Upfront"
                      }
                    },
                    "YZS4YR3ZPHD427K5.VJWZNREJX2": {
                      "priceDimensions": {
                        "YZS4YR3ZPHD427K5.VJWZNREJX2.6YS6EN2CT7": {
                          "unit": "Hrs",
                          "endRange": "Inf",
                          "description": "USD 0.0 per Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied",
                          "appliesTo": [],
                          "rateCode": "YZS4YR3ZPHD427K5.VJWZNREJX2.6YS6EN2CT7",
                          "beginRange": "0",
                          "pricePerUnit": {
                            "USD": "0.0000000000"
                          }
                        },
                        "YZS4YR3ZPHD427K5.VJWZNREJX2.2TG2D8R56U": {
                          "unit": "Quantity",
                          "description": "Upfront Fee",
                          "appliesTo": [],
                          "rateCode": "YZS4YR3ZPHD427K5.VJWZNREJX2.2TG2D8R56U",
                          "pricePerUnit": {
                            "USD": "744"
                          }
                        }
                      },
                      "sku": "YZS4YR3ZPHD427K5",
                      "effectiveDate": "2026-10-07T17:15:22Z",
                      "offerTermCode": "VJWZNREJX2",
                      "termAttributes": {
                        "LeaseContractLength": "1yr",
                        "OfferingClass": "convertible",
                        "PurchaseOption": "All Upfront"
                      }
                    },
                    "YZS4YR3ZPHD427K5.6QCMYABX3D": {
                      "priceDimensions": {
                        "YZS4YR3ZPHD427K5.6QCMYABX3D.6YS6EN2CT7": {
                          "unit": "Hrs",
                          "endRange": "Inf",
                          "description": "USD 0.0 per Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied",
                          "appliesTo": [],
                          "rateCode": "YZS4YR3ZPHD427K5.6QCMYABX3D.6YS6EN2CT7",
                          "beginRange": "0",
                          "pricePerUnit": {
                            "USD": "0.0000000000"
                          }
                        },
                        "YZS4YR3ZPHD427K5.6QCMYABX3D.2TG2D8R56U": {
                          "unit": "Quantity",
                          "description": "Upfront Fee",
                          "appliesTo": [],
                          "rateCode": "YZS4YR3ZPHD427K5.6QCMYABX3D.2TG2D8R56U",
                          "pricePerUnit": {
                            "USD": "647"
                          }
                        }
                      },
                      "sku": "YZS4YR3ZPHD427K5",
                      "effectiveDate": "2026-10-07T17:15:23Z",
                      "offerTermCode": "6QCMYABX3D",
                      "termAttributes": {
                        "LeaseContractLength": "1yr",
                        "OfferingClass": "standard",
                        "PurchaseOption": "All Upfront"
                      }
                    },
                    "YZS4YR3ZPHD427K5.BPH4J8HBKS": {
                      "priceDimensions": {
                        "YZS4YR3ZPHD427K5.BPH4J8HBKS.6YS6EN2CT7": {
                          "unit": "Hrs",
                          "endRange": "Inf",
                          "description": "Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied",
                          "appliesTo": [],
                          "rateCode": "YZS4YR3ZPHD427K5.BPH4J8HBKS.6YS6EN2CT7",
                          "beginRange": "0",
                          "pricePerUnit": {
                            "USD": "0.0543000000"
                          }
                        }
                      },
                      "sku": "YZS4YR3ZPHD427K5",
                      "effectiveDate": "2026-10-07T17:15:21Z",
                      "offerTermCode": "BPH4J8HBKS",
                      "termAttributes": {
                        "LeaseContractLength": "3yr",
                        "OfferingClass": "standard",
                        "PurchaseOption": "No Upfront"
                      }
                    },
                    "YZS4YR3ZPHD427K5.R5XV2EPZQZ": {
                      "priceDimensions": {
                        "YZS4YR3ZPHD427K5.R5XV2EPZQZ.2TG2D8R56U": {
                          "unit": "Quantity",
                          "description": "Upfront Fee",
                          "appliesTo": [],
                          "rateCode": "YZS4YR3ZPHD427K5.R5XV2EPZQZ.2TG2D8R56U",
                          "pricePerUnit": {
                            "USD": "762"
                          }
                        },
                        "YZS4YR3ZPHD427K5.R5XV2EPZQZ.6YS6EN2CT7": {
                          "unit": "Hrs",
                          "endRange": "Inf",
                          "description": "Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied",
                          "appliesTo": [],
                          "rateCode": "YZS4YR3ZPHD427K5.R5XV2EPZQZ.6YS6EN2CT7",
                          "beginRange": "0",
                          "pricePerUnit": {
                            "USD": "0.0290100000"
                          }
                        }
                      },
                      "sku": "YZS4YR3ZPHD427K5",
                      "effectiveDate": "2026-10-07T17:15:21Z",
                      "offerTermCode": "R5XV2EPZQZ",
                      "termAttributes": {
                        "LeaseContractLength": "3yr",
                        "OfferingClass": "convertible",
                        "PurchaseOption": "Partial Upfront"
                      }
                    },
                    "YZS4YR3ZPHD427K5.7NE97W5U4E": {
                      "priceDimensions": {
                        "YZS4YR3ZPHD427K5.7NE97W5U4E.6YS6EN2CT7": {
                          "unit": "Hrs",
                          "endRange": "Inf",
                          "description": "Linux/UNIX (Amazon VPC), m7i-flex.large reserved instance applied",
                          "appliesTo": [],
                          "rateCode": "YZS4YR3ZPHD427K5.7NE97W5U4E.6YS6EN2CT7",
                          "beginRange": "0",
                          "pricePerUnit": {
                            "USD": "0.0909800000"
                          }
                        }
                      },
                      "sku": "YZS4YR3ZPHD427K5",
                      "effectiveDate": "2026-10-07T17:15:22Z",
                      "offerTermCode": "7NE97W5U4E",
                      "termAttributes": {
                        "LeaseContractLength": "1yr",
                        "OfferingClass": "convertible",
                        "PurchaseOption": "No Upfront"
                      }
                    }
                  }
                },
                "version": "20261007165408",
                "publicationDate": "2026-10-07T16:54:08Z"
              }
            ]
          },
          "price_disk": {
            "products": [
              {
                "product": {
                  "productFamily": "Storage",
                  "attributes": {
                    "maxThroughputvolume": "2000 MiB/s",
                    "volumeType": "General Purpose",
                    "maxIopsvolume": "80000",
                    "usagetype": "APS2-EBS:VolumeUsage.gp3",
                    "locationType": "AWS Region",
                    "maxVolumeSize": "64 TiB",
                    "storageMedia": "SSD-backed",
                    "regionCode": "ap-southeast-2",
                    "servicecode": "AmazonEC2",
                    "volumeApiName": "gp3",
                    "location": "Asia Pacific (Sydney)",
                    "servicename": "Amazon Elastic Compute Cloud",
                    "operation": ""
                  },
                  "sku": "QR74UAP3E9WUYT9B"
                },
                "serviceCode": "AmazonEC2",
                "terms": {
                  "OnDemand": {
                    "QR74UAP3E9WUYT9B.JRTCKXETXF": {
                      "priceDimensions": {
                        "QR74UAP3E9WUYT9B.JRTCKXETXF.6YS6EN2CT7": {
                          "unit": "GB-Mo",
                          "endRange": "Inf",
                          "description": "$0.096 per GB-month of General Purpose (gp3) provisioned storage - Asia Pacific (Sydney)",
                          "appliesTo": [],
                          "rateCode": "QR74UAP3E9WUYT9B.JRTCKXETXF.6YS6EN2CT7",
                          "beginRange": "0",
                          "pricePerUnit": {
                            "USD": "0.0960000000"
                          }
                        }
                      },
                      "sku": "QR74UAP3E9WUYT9B",
                      "effectiveDate": "2026-10-01T00:00:00Z",
                      "offerTermCode": "JRTCKXETXF",
                      "termAttributes": {}
                    }
                  }
                },
                "version": "20261007165408",
                "publicationDate": "2026-10-07T16:54:08Z"
              }
            ]
          },
          "price_ipv4": {
            "products": [
              {
                "product": {
                  "attributes": {
                    "regionCode": "ap-southeast-2",
                    "servicecode": "AmazonVPC",
                    "groupDescription": "Hourly charge for In-use Public IPv4 Addresses",
                    "usagetype": "APS2-PublicIPv4:InUseAddress",
                    "locationType": "AWS Region",
                    "location": "Asia Pacific (Sydney)",
                    "servicename": "Amazon Virtual Private Cloud",
                    "operation": "",
                    "group": "VPCPublicIPv4Address"
                  },
                  "sku": "JZP2PURP9VVQ96GH"
                },
                "serviceCode": "AmazonVPC",
                "terms": {
                  "OnDemand": {
                    "JZP2PURP9VVQ96GH.JRTCKXETXF": {
                      "priceDimensions": {
                        "JZP2PURP9VVQ96GH.JRTCKXETXF.6YS6EN2CT7": {
                          "unit": "Hrs",
                          "endRange": "Inf",
                          "description": "$0.005 per In-use public IPv4 address per hour",
                          "appliesTo": [],
                          "rateCode": "JZP2PURP9VVQ96GH.JRTCKXETXF.6YS6EN2CT7",
                          "beginRange": "0",
                          "pricePerUnit": {
                            "USD": "0.0050000000"
                          }
                        }
                      },
                      "sku": "JZP2PURP9VVQ96GH",
                      "effectiveDate": "2026-09-01T00:00:00Z",
                      "offerTermCode": "JRTCKXETXF",
                      "termAttributes": {}
                    }
                  }
                },
                "version": "20260917190528",
                "publicationDate": "2026-09-17T19:05:28Z"
              }
            ]
          },
          "price_s3": {
            "products": [
              {
                "product": {
                  "productFamily": "Storage",
                  "attributes": {
                    "volumeType": "Standard",
                    "storageClass": "General Purpose",
                    "regionCode": "ap-southeast-2",
                    "servicecode": "AmazonS3",
                    "durability": "99.999999999%",
                    "usagetype": "APS2-TimedStorage-ByteHrs",
                    "locationType": "AWS Region",
                    "location": "Asia Pacific (Sydney)",
                    "servicename": "Amazon Simple Storage Service",
                    "availability": "99.99%",
                    "operation": ""
                  },
                  "sku": "5QVJMK36NJC9G6DC"
                },
                "serviceCode": "AmazonS3",
                "terms": {
                  "OnDemand": {
                    "5QVJMK36NJC9G6DC.JRTCKXETXF": {
                      "priceDimensions": {
                        "5QVJMK36NJC9G6DC.JRTCKXETXF.PGHJ3S3EYE": {
                          "unit": "GB-Mo",
                          "endRange": "51200",
                          "description": "$0.025 per GB - first 50 TB / month of storage used",
                          "appliesTo": [],
                          "rateCode": "5QVJMK36NJC9G6DC.JRTCKXETXF.PGHJ3S3EYE",
                          "beginRange": "0",
                          "pricePerUnit": {
                            "USD": "0.0250000000"
                          }
                        },
                        "5QVJMK36NJC9G6DC.JRTCKXETXF.D42MF2PVJS": {
                          "unit": "GB-Mo",
                          "endRange": "512000",
                          "description": "$0.024 per GB - next 450 TB / month of storage used",
                          "appliesTo": [],
                          "rateCode": "5QVJMK36NJC9G6DC.JRTCKXETXF.D42MF2PVJS",
                          "beginRange": "51200",
                          "pricePerUnit": {
                            "USD": "0.0240000000"
                          }
                        },
                        "5QVJMK36NJC9G6DC.JRTCKXETXF.PXJDJ3YRG3": {
                          "unit": "GB-Mo",
                          "endRange": "Inf",
                          "description": "$0.023 per GB - storage used / month over 500 TB",
                          "appliesTo": [],
                          "rateCode": "5QVJMK36NJC9G6DC.JRTCKXETXF.PXJDJ3YRG3",
                          "beginRange": "512000",
                          "pricePerUnit": {
                            "USD": "0.0230000000"
                          }
                        }
                      },
                      "sku": "5QVJMK36NJC9G6DC",
                      "effectiveDate": "2026-09-01T00:00:00Z",
                      "offerTermCode": "JRTCKXETXF",
                      "termAttributes": {}
                    }
                  }
                },
                "version": "20260928230416",
                "publicationDate": "2026-09-28T23:04:16Z"
              }
            ]
          }
        },
        "api_calls": [
          {
            "service": "freetier",
            "operation": "GetAccountPlanState",
            "status": "success"
          },
          {
            "service": "ec2",
            "operation": "DescribeInstances",
            "status": "success",
            "n_items": {
              "Reservations": 1
            }
          },
          {
            "service": "ec2",
            "operation": "DescribeVolumes",
            "status": "success",
            "n_items": {
              "Volumes": 1
            }
          },
          {
            "service": "ec2",
            "operation": "DescribeImages",
            "status": "success",
            "n_items": {
              "Images": 1
            }
          },
          {
            "service": "ec2",
            "operation": "DescribeSubnets",
            "status": "success",
            "n_items": {
              "Subnets": 1
            }
          },
          {
            "service": "ec2",
            "operation": "DescribeSecurityGroups",
            "status": "success",
            "n_items": {
              "SecurityGroups": 1
            }
          },
          {
            "service": "ec2",
            "operation": "DescribeRouteTables",
            "status": "success",
            "n_items": {
              "RouteTables": 1
            }
          },
          {
            "service": "iam",
            "operation": "GetInstanceProfile",
            "status": "success"
          },
          {
            "service": "s3",
            "operation": "GetBucketVersioning",
            "status": "success"
          },
          {
            "service": "pricing",
            "operation": "GetProducts",
            "status": "success",
            "n_items": {
              "PriceList": 1
            }
          },
          {
            "service": "pricing",
            "operation": "GetProducts",
            "status": "success",
            "n_items": {
              "PriceList": 1
            }
          },
          {
            "service": "pricing",
            "operation": "GetProducts",
            "status": "success",
            "n_items": {
              "PriceList": 1
            }
          },
          {
            "service": "pricing",
            "operation": "GetProducts",
            "status": "success",
            "n_items": {
              "PriceList": 1
            }
          }
        ]
      },
      "isError": false
    }
  },
  "preadmission-feasibility.json": {
    "sha256": "07827d4b05e6b147c6d1dedc312e400f27146962ab1412739ba67a24b418f1e8",
    "result": {
      "kind": "REVIEW_ESTIMATE_NOT_LAUNCH_OR_FINAL_BILL",
      "as_of_utc": "2026-10-07T20:44:06.014656+00:00",
      "original_start_utc": "2026-10-07T15:24:23.810674+00:00",
      "operational_deadline_utc": "2026-10-22T15:24:23.810674+00:00",
      "original_time_admission_cutoff_utc": "2026-10-22T14:54:23.810674+00:00",
      "conservative_cost_admission_cutoff_utc": "2026-10-21T01:19:40.337448+00:00",
      "remaining_hours_to_hard_deadline": 354.671610005,
      "remaining_originals": 1499,
      "unchanged_budget_usd": 65,
      "unchanged_admission_guard_usd": 55,
      "cold_handover_reserve_usd": 1.25,
      "host_scope": "one fresh m7i-flex.large/160GiB plus original stopped disk <=48h",
      "current_rates": {
        "compute": 0.1197,
        "disk": 0.096,
        "ipv4": 0.005,
        "s3": 0.025
      },
      "rates_match_accepted": true,
      "aws_readonly_calls": 7,
      "aws_mutations": 0,
      "original_host_state": "stopped",
      "reported_credit_usd": 119.37,
      "plan": "FREE",
      "maximum_original_360h_conservative_usd": 60.47676712328767,
      "estimates": {
        "historical_pilot_median_reference": {
          "remaining_execution_hours": 255.4069478198611,
          "setup_hours_allowance": 2,
          "finish_if_setup_begins_as_of_utc": "2026-10-18T14:08:31.026807+00:00",
          "conservative_committed_usd_at_finish_plus_30min": 46.37417921293988,
          "fits_cost_admission_guard": true,
          "fits_original_time_cutoff": true,
          "latest_setup_start_utc_conservative": "2026-10-10T07:55:15.325297+00:00"
        },
        "four_local_amendment_mean_reference": {
          "remaining_execution_hours": 285.23326436093305,
          "setup_hours_allowance": 2,
          "finish_if_setup_begins_as_of_utc": "2026-10-19T19:58:05.766355+00:00",
          "conservative_committed_usd_at_finish_plus_30min": 50.7210992720157,
          "fits_cost_admission_guard": true,
          "fits_original_time_cutoff": true,
          "latest_setup_start_utc_conservative": "2026-10-09T02:05:40.585749+00:00"
        },
        "planning_12_days": {
          "remaining_execution_hours": 288.0,
          "setup_hours_allowance": 2,
          "finish_if_setup_begins_as_of_utc": "2026-10-19T22:44:06.014656+00:00",
          "conservative_committed_usd_at_finish_plus_30min": 51.12432635610691,
          "fits_cost_admission_guard": true,
          "fits_original_time_cutoff": true,
          "latest_setup_start_utc_conservative": "2026-10-08T23:19:40.337448+00:00"
        },
        "planning_13_days_conservative": {
          "remaining_execution_hours": 312.0,
          "setup_hours_allowance": 2,
          "finish_if_setup_begins_as_of_utc": "2026-10-20T22:44:06.014656+00:00",
          "conservative_committed_usd_at_finish_plus_30min": 54.62211265747678,
          "fits_cost_admission_guard": true,
          "fits_original_time_cutoff": true,
          "latest_setup_start_utc_conservative": "2026-10-07T23:19:40.337448+00:00"
        }
      },
      "storage_gib": {
        "raw_projection_remaining": 23.329313575522974,
        "backup_projection_remaining": 8.65345248960269,
        "archive_projection_remaining": 5.55219460084724,
        "working_allowance": 50,
        "backup_allowance": 50,
        "os_images": 25,
        "headroom": 35,
        "cloud_versions_limit": 30
      },
      "limitations": [
        "Pilot median and four-calibration mean are references, not whole-bank measurements.",
        "12-13 days remains a planning range; no completion guarantee or limit extension.",
        "Elapsed-clock cost accounting conservatively charges paused time; do not reset it.",
        "Old disk/early-host spending stays reserved inside the existing guard; no new budget.",
        "Retained disk review: 2026-10-09T15:57:46Z. Indefinite retention is not funded.",
        "Credits/billing can lag; prices, credits and fit need a fresh predeployment check.",
        "Request/transfer allowance remains $5; taxes and unrelated project costs excluded."
      ]
    }
  },
  "preadmission-credits.json": {
    "sha256": "2776c23baf05e2f2acc7c72e54fe121cbbd6427c4ed50ee0122ebc20b9c13610",
    "result": {
      "content": [
        {
          "type": "text",
          "text": "{\"status\": \"success\", \"stdout\": \"\", \"stderr\": null, \"return_value\": {\"accountId\": \"803656589923\", \"accountPlanType\": \"FREE\", \"accountPlanStatus\": \"ACTIVE\", \"accountPlanRemainingCredits\": {\"amount\": 119.37, \"unit\": \"USD\"}, \"accountPlanExpirationDate\": \"2027-04-05T13:45:14.308000+00:00\"}, \"warning\": null, \"api_calls\": [{\"service\": \"freetier\", \"operation\": \"GetAccountPlanState\", \"status\": \"success\"}]}"
        }
      ],
      "structuredContent": {
        "status": "success",
        "stdout": "",
        "return_value": {
          "accountId": "803656589923",
          "accountPlanType": "FREE",
          "accountPlanStatus": "ACTIVE",
          "accountPlanRemainingCredits": {
            "amount": 119.37,
            "unit": "USD"
          },
          "accountPlanExpirationDate": "2027-04-05T13:45:14.308000+00:00"
        },
        "api_calls": [
          {
            "service": "freetier",
            "operation": "GetAccountPlanState",
            "status": "success"
          }
        ]
      },
      "isError": false
    }
  },
  "actual-deployment-binding.json": {
    "sha256": "c9ac10655d79d846de978f1e0117f5e434efdb2ac693a35af5881b2cc754148f",
    "result": {
      "kind": "ACTUAL_FRESH_HOST_DEPLOYMENT_NOT_MAIN_LAUNCH",
      "at_utc": "2026-10-07T20:29:19.816285+00:00",
      "instance_id": "i-034252c3e9b083abf",
      "launch_time_utc": "2026-10-07T20:26:09+00:00",
      "run_id": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9",
      "package_hash": "c308222096cf3c9026aa275e73fd7d75bce386e641824330f385dab02d4b609f",
      "request_sha256": "acb170be3dff0243c415571315417d7e3c664bf6f1faf307b58423765b52dc55",
      "authorization_statement_sha256": "4431bb9bb814f3e4f9df4a4bf24d9d88093a9fded2e476f062598935e6e223b5",
      "main_admitted": false,
      "operational_clock_reset": false,
      "hard_deadline_utc": "2026-10-22T15:24:23.810674Z"
    }
  },
  "fresh-and-old-host-state.json": {
    "sha256": "d82e3e546b150d1548ffa08fb7f78cdb8615654a54d2f97156d36d833a57602e",
    "result": {
      "content": [
        {
          "type": "text",
          "text": "{\"status\": \"success\", \"stdout\": \"\", \"stderr\": null, \"return_value\": {\"Reservations\": [{\"ReservationId\": \"r-09dd2a8d6fada358a\", \"OwnerId\": \"803656589923\", \"Groups\": [], \"Instances\": [{\"Architecture\": \"x86_64\", \"BlockDeviceMappings\": [{\"DeviceName\": \"/dev/sda1\", \"Ebs\": {\"AttachTime\": \"2026-10-07T15:29:06+00:00\", \"DeleteOnTermination\": false, \"Status\": \"attached\", \"VolumeId\": \"vol-07baf9132bce08e77\", \"EbsCardIndex\": 0}}], \"ClientToken\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\", \"EbsOptimized\": false, \"EnaSupport\": true, \"Hypervisor\": \"xen\", \"IamInstanceProfile\": {\"Arn\": \"arn:aws:iam::803656589923:instance-profile/FYP-p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\", \"Id\": \"AIPA3WHNKMJRVRF7W6G3I\"}, \"NetworkInterfaces\": [{\"Attachment\": {\"AttachTime\": \"2026-10-07T15:29:05+00:00\", \"AttachmentId\": \"eni-attach-0813fcecf35d7cf54\", \"DeleteOnTermination\": true, \"DeviceIndex\": 0, \"Status\": \"attached\", \"NetworkCardIndex\": 0}, \"Description\": \"\", \"Groups\": [{\"GroupId\": \"sg-076d87ac5db0a6f52\", \"GroupName\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}], \"Ipv6Addresses\": [], \"MacAddress\": \"02:ff:c8:a3:48:07\", \"NetworkInterfaceId\": \"eni-0b2d2e6ce97e47a2f\", \"OwnerId\": \"803656589923\", \"PrivateDnsName\": \"ip-172-31-4-109.ap-southeast-2.compute.internal\", \"PrivateIpAddress\": \"172.31.4.109\", \"PrivateIpAddresses\": [{\"Primary\": true, \"PrivateDnsName\": \"ip-172-31-4-109.ap-southeast-2.compute.internal\", \"PrivateIpAddress\": \"172.31.4.109\"}], \"SourceDestCheck\": true, \"Status\": \"in-use\", \"SubnetId\": \"subnet-05c5c729c83dc651b\", \"VpcId\": \"vpc-0c74e59331cbc1caa\", \"InterfaceType\": \"interface\", \"Operator\": {\"Managed\": false}}], \"RootDeviceName\": \"/dev/sda1\", \"RootDeviceType\": \"ebs\", \"SecurityGroups\": [{\"GroupId\": \"sg-076d87ac5db0a6f52\", \"GroupName\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}], \"SourceDestCheck\": true, \"StateReason\": {\"Code\": \"Client.UserInitiatedShutdown\", \"Message\": \"Client.UserInitiatedShutdown: User initiated shutdown\"}, \"Tags\": [{\"Key\": \"research.owner\", \"Value\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}, {\"Key\": \"Name\", \"Value\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}, {\"Key\": \"research.stage\", \"Value\": \"8.5\"}], \"VirtualizationType\": \"hvm\", \"CpuOptions\": {\"CoreCount\": 1, \"ThreadsPerCore\": 2}, \"CapacityReservationSpecification\": {\"CapacityReservationPreference\": \"open\"}, \"HibernationOptions\": {\"Configured\": false}, \"MetadataOptions\": {\"State\": \"applied\", \"HttpTokens\": \"required\", \"HttpPutResponseHopLimit\": 1, \"HttpEndpoint\": \"enabled\", \"HttpProtocolIpv6\": \"disabled\", \"InstanceMetadataTags\": \"disabled\"}, \"EnclaveOptions\": {\"Enabled\": false}, \"BootMode\": \"uefi-preferred\", \"PlatformDetails\": \"Linux/UNIX\", \"UsageOperation\": \"RunInstances\", \"UsageOperationUpdateTime\": \"2026-10-07T15:29:05+00:00\", \"PrivateDnsNameOptions\": {\"HostnameType\": \"ip-name\", \"EnableResourceNameDnsARecord\": false, \"EnableResourceNameDnsAAAARecord\": false}, \"MaintenanceOptions\": {\"AutoRecovery\": \"default\", \"RebootMigration\": \"default\"}, \"CurrentInstanceBootMode\": \"uefi\", \"NetworkPerformanceOptions\": {\"BandwidthWeighting\": \"default\"}, \"Operator\": {\"Managed\": false, \"HiddenByDefault\": false}, \"InstanceId\": \"i-0a6196aff6f8098ac\", \"ImageId\": \"ami-090b1140798d2d006\", \"State\": {\"Code\": 80, \"Name\": \"stopped\"}, \"PrivateDnsName\": \"ip-172-31-4-109.ap-southeast-2.compute.internal\", \"PublicDnsName\": \"\", \"StateTransitionReason\": \"User initiated (2026-10-07 15:57:46 GMT)\", \"AmiLaunchIndex\": 0, \"ProductCodes\": [], \"InstanceType\": \"m7i-flex.large\", \"LaunchTime\": \"2026-10-07T15:29:05+00:00\", \"Placement\": {\"AvailabilityZoneId\": \"apse2-az1\", \"GroupName\": \"\", \"Tenancy\": \"default\", \"AvailabilityZone\": \"ap-southeast-2a\"}, \"Monitoring\": {\"State\": \"disabled\"}, \"SubnetId\": \"subnet-05c5c729c83dc651b\", \"VpcId\": \"vpc-0c74e59331cbc1caa\", \"PrivateIpAddress\": \"172.31.4.109\"}]}, {\"ReservationId\": \"r-029c463661cb81945\", \"OwnerId\": \"803656589923\", \"Groups\": [], \"Instances\": [{\"Architecture\": \"x86_64\", \"BlockDeviceMappings\": [{\"DeviceName\": \"/dev/sda1\", \"Ebs\": {\"AttachTime\": \"2026-10-07T20:26:10+00:00\", \"DeleteOnTermination\": false, \"Status\": \"attached\", \"VolumeId\": \"vol-0f667d76019af7a47\", \"EbsCardIndex\": 0}}], \"ClientToken\": \"p85c1-01a116f7-3b82-7a79-8653-3aee62dc99e9\", \"EbsOptimized\": false, \"EnaSupport\": true, \"Hypervisor\": \"xen\", \"IamInstanceProfile\": {\"Arn\": \"arn:aws:iam::803656589923:instance-profile/FYP-p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\", \"Id\": \"AIPA3WHNKMJRVRF7W6G3I\"}, \"NetworkInterfaces\": [{\"Association\": {\"IpOwnerId\": \"amazon\", \"PublicDnsName\": \"ec2-3-27-213-30.ap-southeast-2.compute.amazonaws.com\", \"PublicIp\": \"3.27.213.30\"}, \"Attachment\": {\"AttachTime\": \"2026-10-07T20:26:09+00:00\", \"AttachmentId\": \"eni-attach-0c8df59a92d792d75\", \"DeleteOnTermination\": true, \"DeviceIndex\": 0, \"Status\": \"attached\", \"NetworkCardIndex\": 0}, \"Description\": \"\", \"Groups\": [{\"GroupId\": \"sg-076d87ac5db0a6f52\", \"GroupName\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}], \"Ipv6Addresses\": [], \"MacAddress\": \"02:ff:ca:bb:35:0f\", \"NetworkInterfaceId\": \"eni-03e249c75d5faed3e\", \"OwnerId\": \"803656589923\", \"PrivateDnsName\": \"ip-172-31-12-61.ap-southeast-2.compute.internal\", \"PrivateIpAddress\": \"172.31.12.61\", \"PrivateIpAddresses\": [{\"Association\": {\"IpOwnerId\": \"amazon\", \"PublicDnsName\": \"ec2-3-27-213-30.ap-southeast-2.compute.amazonaws.com\", \"PublicIp\": \"3.27.213.30\"}, \"Primary\": true, \"PrivateDnsName\": \"ip-172-31-12-61.ap-southeast-2.compute.internal\", \"PrivateIpAddress\": \"172.31.12.61\"}], \"SourceDestCheck\": true, \"Status\": \"in-use\", \"SubnetId\": \"subnet-05c5c729c83dc651b\", \"VpcId\": \"vpc-0c74e59331cbc1caa\", \"InterfaceType\": \"interface\", \"Operator\": {\"Managed\": false}}], \"RootDeviceName\": \"/dev/sda1\", \"RootDeviceType\": \"ebs\", \"SecurityGroups\": [{\"GroupId\": \"sg-076d87ac5db0a6f52\", \"GroupName\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}], \"SourceDestCheck\": true, \"Tags\": [{\"Key\": \"research.stage\", \"Value\": \"8.5\"}, {\"Key\": \"Name\", \"Value\": \"p85-continuation-v1\"}, {\"Key\": \"research.owner\", \"Value\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}, {\"Key\": \"research.package\", \"Value\": \"phase85-continuation-v1\"}], \"VirtualizationType\": \"hvm\", \"CpuOptions\": {\"CoreCount\": 1, \"ThreadsPerCore\": 2}, \"CapacityReservationSpecification\": {\"CapacityReservationPreference\": \"open\"}, \"HibernationOptions\": {\"Configured\": false}, \"MetadataOptions\": {\"State\": \"applied\", \"HttpTokens\": \"required\", \"HttpPutResponseHopLimit\": 1, \"HttpEndpoint\": \"enabled\", \"HttpProtocolIpv6\": \"disabled\", \"InstanceMetadataTags\": \"disabled\"}, \"EnclaveOptions\": {\"Enabled\": false}, \"BootMode\": \"uefi-preferred\", \"PlatformDetails\": \"Linux/UNIX\", \"UsageOperation\": \"RunInstances\", \"UsageOperationUpdateTime\": \"2026-10-07T20:26:09+00:00\", \"PrivateDnsNameOptions\": {\"HostnameType\": \"ip-name\", \"EnableResourceNameDnsARecord\": false, \"EnableResourceNameDnsAAAARecord\": false}, \"MaintenanceOptions\": {\"AutoRecovery\": \"default\", \"RebootMigration\": \"default\"}, \"CurrentInstanceBootMode\": \"uefi\", \"NetworkPerformanceOptions\": {\"BandwidthWeighting\": \"default\"}, \"Operator\": {\"Managed\": false, \"HiddenByDefault\": false}, \"InstanceId\": \"i-034252c3e9b083abf\", \"ImageId\": \"ami-090b1140798d2d006\", \"State\": {\"Code\": 16, \"Name\": \"running\"}, \"PrivateDnsName\": \"ip-172-31-12-61.ap-southeast-2.compute.internal\", \"PublicDnsName\": \"ec2-3-27-213-30.ap-southeast-2.compute.amazonaws.com\", \"StateTransitionReason\": \"\", \"AmiLaunchIndex\": 0, \"ProductCodes\": [], \"InstanceType\": \"m7i-flex.large\", \"LaunchTime\": \"2026-10-07T20:26:09+00:00\", \"Placement\": {\"AvailabilityZoneId\": \"apse2-az1\", \"GroupName\": \"\", \"Tenancy\": \"default\", \"AvailabilityZone\": \"ap-southeast-2a\"}, \"Monitoring\": {\"State\": \"disabled\"}, \"SubnetId\": \"subnet-05c5c729c83dc651b\", \"VpcId\": \"vpc-0c74e59331cbc1caa\", \"PrivateIpAddress\": \"172.31.12.61\", \"PublicIpAddress\": \"3.27.213.30\"}]}]}, \"warning\": null, \"api_calls\": [{\"service\": \"ec2\", \"operation\": \"DescribeInstances\", \"status\": \"success\", \"n_items\": {\"Reservations\": 2}}]}"
        }
      ],
      "structuredContent": {
        "status": "success",
        "stdout": "",
        "return_value": {
          "Reservations": [
            {
              "ReservationId": "r-09dd2a8d6fada358a",
              "OwnerId": "803656589923",
              "Groups": [],
              "Instances": [
                {
                  "Architecture": "x86_64",
                  "BlockDeviceMappings": [
                    {
                      "DeviceName": "/dev/sda1",
                      "Ebs": {
                        "AttachTime": "2026-10-07T15:29:06+00:00",
                        "DeleteOnTermination": false,
                        "Status": "attached",
                        "VolumeId": "vol-07baf9132bce08e77",
                        "EbsCardIndex": 0
                      }
                    }
                  ],
                  "ClientToken": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9",
                  "EbsOptimized": false,
                  "EnaSupport": true,
                  "Hypervisor": "xen",
                  "IamInstanceProfile": {
                    "Arn": "arn:aws:iam::803656589923:instance-profile/FYP-p85-01a116f7-3b82-7a79-8653-3aee62dc99e9",
                    "Id": "AIPA3WHNKMJRVRF7W6G3I"
                  },
                  "NetworkInterfaces": [
                    {
                      "Attachment": {
                        "AttachTime": "2026-10-07T15:29:05+00:00",
                        "AttachmentId": "eni-attach-0813fcecf35d7cf54",
                        "DeleteOnTermination": true,
                        "DeviceIndex": 0,
                        "Status": "attached",
                        "NetworkCardIndex": 0
                      },
                      "Description": "",
                      "Groups": [
                        {
                          "GroupId": "sg-076d87ac5db0a6f52",
                          "GroupName": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                        }
                      ],
                      "Ipv6Addresses": [],
                      "MacAddress": "02:ff:c8:a3:48:07",
                      "NetworkInterfaceId": "eni-0b2d2e6ce97e47a2f",
                      "OwnerId": "803656589923",
                      "PrivateDnsName": "ip-172-31-4-109.ap-southeast-2.compute.internal",
                      "PrivateIpAddress": "172.31.4.109",
                      "PrivateIpAddresses": [
                        {
                          "Primary": true,
                          "PrivateDnsName": "ip-172-31-4-109.ap-southeast-2.compute.internal",
                          "PrivateIpAddress": "172.31.4.109"
                        }
                      ],
                      "SourceDestCheck": true,
                      "Status": "in-use",
                      "SubnetId": "subnet-05c5c729c83dc651b",
                      "VpcId": "vpc-0c74e59331cbc1caa",
                      "InterfaceType": "interface",
                      "Operator": {
                        "Managed": false
                      }
                    }
                  ],
                  "RootDeviceName": "/dev/sda1",
                  "RootDeviceType": "ebs",
                  "SecurityGroups": [
                    {
                      "GroupId": "sg-076d87ac5db0a6f52",
                      "GroupName": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                    }
                  ],
                  "SourceDestCheck": true,
                  "StateReason": {
                    "Code": "Client.UserInitiatedShutdown",
                    "Message": "Client.UserInitiatedShutdown: User initiated shutdown"
                  },
                  "Tags": [
                    {
                      "Key": "research.owner",
                      "Value": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                    },
                    {
                      "Key": "Name",
                      "Value": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                    },
                    {
                      "Key": "research.stage",
                      "Value": "8.5"
                    }
                  ],
                  "VirtualizationType": "hvm",
                  "CpuOptions": {
                    "CoreCount": 1,
                    "ThreadsPerCore": 2
                  },
                  "CapacityReservationSpecification": {
                    "CapacityReservationPreference": "open"
                  },
                  "HibernationOptions": {
                    "Configured": false
                  },
                  "MetadataOptions": {
                    "State": "applied",
                    "HttpTokens": "required",
                    "HttpPutResponseHopLimit": 1,
                    "HttpEndpoint": "enabled",
                    "HttpProtocolIpv6": "disabled",
                    "InstanceMetadataTags": "disabled"
                  },
                  "EnclaveOptions": {
                    "Enabled": false
                  },
                  "BootMode": "uefi-preferred",
                  "PlatformDetails": "Linux/UNIX",
                  "UsageOperation": "RunInstances",
                  "UsageOperationUpdateTime": "2026-10-07T15:29:05+00:00",
                  "PrivateDnsNameOptions": {
                    "HostnameType": "ip-name",
                    "EnableResourceNameDnsARecord": false,
                    "EnableResourceNameDnsAAAARecord": false
                  },
                  "MaintenanceOptions": {
                    "AutoRecovery": "default",
                    "RebootMigration": "default"
                  },
                  "CurrentInstanceBootMode": "uefi",
                  "NetworkPerformanceOptions": {
                    "BandwidthWeighting": "default"
                  },
                  "Operator": {
                    "Managed": false,
                    "HiddenByDefault": false
                  },
                  "InstanceId": "i-0a6196aff6f8098ac",
                  "ImageId": "ami-090b1140798d2d006",
                  "State": {
                    "Code": 80,
                    "Name": "stopped"
                  },
                  "PrivateDnsName": "ip-172-31-4-109.ap-southeast-2.compute.internal",
                  "PublicDnsName": "",
                  "StateTransitionReason": "User initiated (2026-10-07 15:57:46 GMT)",
                  "AmiLaunchIndex": 0,
                  "ProductCodes": [],
                  "InstanceType": "m7i-flex.large",
                  "LaunchTime": "2026-10-07T15:29:05+00:00",
                  "Placement": {
                    "AvailabilityZoneId": "apse2-az1",
                    "GroupName": "",
                    "Tenancy": "default",
                    "AvailabilityZone": "ap-southeast-2a"
                  },
                  "Monitoring": {
                    "State": "disabled"
                  },
                  "SubnetId": "subnet-05c5c729c83dc651b",
                  "VpcId": "vpc-0c74e59331cbc1caa",
                  "PrivateIpAddress": "172.31.4.109"
                }
              ]
            },
            {
              "ReservationId": "r-029c463661cb81945",
              "OwnerId": "803656589923",
              "Groups": [],
              "Instances": [
                {
                  "Architecture": "x86_64",
                  "BlockDeviceMappings": [
                    {
                      "DeviceName": "/dev/sda1",
                      "Ebs": {
                        "AttachTime": "2026-10-07T20:26:10+00:00",
                        "DeleteOnTermination": false,
                        "Status": "attached",
                        "VolumeId": "vol-0f667d76019af7a47",
                        "EbsCardIndex": 0
                      }
                    }
                  ],
                  "ClientToken": "p85c1-01a116f7-3b82-7a79-8653-3aee62dc99e9",
                  "EbsOptimized": false,
                  "EnaSupport": true,
                  "Hypervisor": "xen",
                  "IamInstanceProfile": {
                    "Arn": "arn:aws:iam::803656589923:instance-profile/FYP-p85-01a116f7-3b82-7a79-8653-3aee62dc99e9",
                    "Id": "AIPA3WHNKMJRVRF7W6G3I"
                  },
                  "NetworkInterfaces": [
                    {
                      "Association": {
                        "IpOwnerId": "amazon",
                        "PublicDnsName": "ec2-3-27-213-30.ap-southeast-2.compute.amazonaws.com",
                        "PublicIp": "3.27.213.30"
                      },
                      "Attachment": {
                        "AttachTime": "2026-10-07T20:26:09+00:00",
                        "AttachmentId": "eni-attach-0c8df59a92d792d75",
                        "DeleteOnTermination": true,
                        "DeviceIndex": 0,
                        "Status": "attached",
                        "NetworkCardIndex": 0
                      },
                      "Description": "",
                      "Groups": [
                        {
                          "GroupId": "sg-076d87ac5db0a6f52",
                          "GroupName": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                        }
                      ],
                      "Ipv6Addresses": [],
                      "MacAddress": "02:ff:ca:bb:35:0f",
                      "NetworkInterfaceId": "eni-03e249c75d5faed3e",
                      "OwnerId": "803656589923",
                      "PrivateDnsName": "ip-172-31-12-61.ap-southeast-2.compute.internal",
                      "PrivateIpAddress": "172.31.12.61",
                      "PrivateIpAddresses": [
                        {
                          "Association": {
                            "IpOwnerId": "amazon",
                            "PublicDnsName": "ec2-3-27-213-30.ap-southeast-2.compute.amazonaws.com",
                            "PublicIp": "3.27.213.30"
                          },
                          "Primary": true,
                          "PrivateDnsName": "ip-172-31-12-61.ap-southeast-2.compute.internal",
                          "PrivateIpAddress": "172.31.12.61"
                        }
                      ],
                      "SourceDestCheck": true,
                      "Status": "in-use",
                      "SubnetId": "subnet-05c5c729c83dc651b",
                      "VpcId": "vpc-0c74e59331cbc1caa",
                      "InterfaceType": "interface",
                      "Operator": {
                        "Managed": false
                      }
                    }
                  ],
                  "RootDeviceName": "/dev/sda1",
                  "RootDeviceType": "ebs",
                  "SecurityGroups": [
                    {
                      "GroupId": "sg-076d87ac5db0a6f52",
                      "GroupName": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                    }
                  ],
                  "SourceDestCheck": true,
                  "Tags": [
                    {
                      "Key": "research.stage",
                      "Value": "8.5"
                    },
                    {
                      "Key": "Name",
                      "Value": "p85-continuation-v1"
                    },
                    {
                      "Key": "research.owner",
                      "Value": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                    },
                    {
                      "Key": "research.package",
                      "Value": "phase85-continuation-v1"
                    }
                  ],
                  "VirtualizationType": "hvm",
                  "CpuOptions": {
                    "CoreCount": 1,
                    "ThreadsPerCore": 2
                  },
                  "CapacityReservationSpecification": {
                    "CapacityReservationPreference": "open"
                  },
                  "HibernationOptions": {
                    "Configured": false
                  },
                  "MetadataOptions": {
                    "State": "applied",
                    "HttpTokens": "required",
                    "HttpPutResponseHopLimit": 1,
                    "HttpEndpoint": "enabled",
                    "HttpProtocolIpv6": "disabled",
                    "InstanceMetadataTags": "disabled"
                  },
                  "EnclaveOptions": {
                    "Enabled": false
                  },
                  "BootMode": "uefi-preferred",
                  "PlatformDetails": "Linux/UNIX",
                  "UsageOperation": "RunInstances",
                  "UsageOperationUpdateTime": "2026-10-07T20:26:09+00:00",
                  "PrivateDnsNameOptions": {
                    "HostnameType": "ip-name",
                    "EnableResourceNameDnsARecord": false,
                    "EnableResourceNameDnsAAAARecord": false
                  },
                  "MaintenanceOptions": {
                    "AutoRecovery": "default",
                    "RebootMigration": "default"
                  },
                  "CurrentInstanceBootMode": "uefi",
                  "NetworkPerformanceOptions": {
                    "BandwidthWeighting": "default"
                  },
                  "Operator": {
                    "Managed": false,
                    "HiddenByDefault": false
                  },
                  "InstanceId": "i-034252c3e9b083abf",
                  "ImageId": "ami-090b1140798d2d006",
                  "State": {
                    "Code": 16,
                    "Name": "running"
                  },
                  "PrivateDnsName": "ip-172-31-12-61.ap-southeast-2.compute.internal",
                  "PublicDnsName": "ec2-3-27-213-30.ap-southeast-2.compute.amazonaws.com",
                  "StateTransitionReason": "",
                  "AmiLaunchIndex": 0,
                  "ProductCodes": [],
                  "InstanceType": "m7i-flex.large",
                  "LaunchTime": "2026-10-07T20:26:09+00:00",
                  "Placement": {
                    "AvailabilityZoneId": "apse2-az1",
                    "GroupName": "",
                    "Tenancy": "default",
                    "AvailabilityZone": "ap-southeast-2a"
                  },
                  "Monitoring": {
                    "State": "disabled"
                  },
                  "SubnetId": "subnet-05c5c729c83dc651b",
                  "VpcId": "vpc-0c74e59331cbc1caa",
                  "PrivateIpAddress": "172.31.12.61",
                  "PublicIpAddress": "3.27.213.30"
                }
              ]
            }
          ]
        },
        "api_calls": [
          {
            "service": "ec2",
            "operation": "DescribeInstances",
            "status": "success",
            "n_items": {
              "Reservations": 2
            }
          }
        ]
      },
      "isError": false
    }
  },
  "volume-ownership-encryption.json": {
    "sha256": "30269303d4e264d565dc2d22a2ddb4395fdee7ddee5c6e1692571c86575e0e63",
    "result": {
      "content": [
        {
          "type": "text",
          "text": "{\"status\": \"success\", \"stdout\": \"\", \"stderr\": null, \"return_value\": {\"Volumes\": [{\"AvailabilityZoneId\": \"apse2-az1\", \"Iops\": 3000, \"Tags\": [{\"Key\": \"Name\", \"Value\": \"p85-continuation-v1\"}, {\"Key\": \"research.stage\", \"Value\": \"8.5\"}, {\"Key\": \"research.package\", \"Value\": \"phase85-continuation-v1\"}, {\"Key\": \"research.owner\", \"Value\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}], \"VolumeType\": \"gp3\", \"MultiAttachEnabled\": false, \"Throughput\": 125, \"Operator\": {\"Managed\": false, \"HiddenByDefault\": false}, \"VolumeArn\": \"arn:aws:ec2:ap-southeast-2:803656589923:volume/vol-0f667d76019af7a47\", \"OwnerId\": \"803656589923\", \"VolumeId\": \"vol-0f667d76019af7a47\", \"Size\": 160, \"SnapshotId\": \"snap-04f8536d791ceaecf\", \"AvailabilityZone\": \"ap-southeast-2a\", \"State\": \"in-use\", \"CreateTime\": \"2026-10-07T20:26:10.176000+00:00\", \"Attachments\": [{\"DeleteOnTermination\": false, \"EbsCardIndex\": 0, \"VolumeId\": \"vol-0f667d76019af7a47\", \"InstanceId\": \"i-034252c3e9b083abf\", \"Device\": \"/dev/sda1\", \"State\": \"attached\", \"AttachTime\": \"2026-10-07T20:26:10+00:00\"}], \"Encrypted\": true, \"KmsKeyId\": \"arn:aws:kms:ap-southeast-2:803656589923:key/1ad9e0e5-ad7c-4f52-8b41-50c266898626\"}, {\"AvailabilityZoneId\": \"apse2-az1\", \"Iops\": 3000, \"Tags\": [{\"Key\": \"Name\", \"Value\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}, {\"Key\": \"research.owner\", \"Value\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}, {\"Key\": \"research.stage\", \"Value\": \"8.5\"}], \"VolumeType\": \"gp3\", \"MultiAttachEnabled\": false, \"Throughput\": 125, \"Operator\": {\"Managed\": false, \"HiddenByDefault\": false}, \"VolumeArn\": \"arn:aws:ec2:ap-southeast-2:803656589923:volume/vol-07baf9132bce08e77\", \"OwnerId\": \"803656589923\", \"VolumeId\": \"vol-07baf9132bce08e77\", \"Size\": 160, \"SnapshotId\": \"snap-04f8536d791ceaecf\", \"AvailabilityZone\": \"ap-southeast-2a\", \"State\": \"in-use\", \"CreateTime\": \"2026-10-07T15:29:06.157000+00:00\", \"Attachments\": [{\"DeleteOnTermination\": false, \"EbsCardIndex\": 0, \"VolumeId\": \"vol-07baf9132bce08e77\", \"InstanceId\": \"i-0a6196aff6f8098ac\", \"Device\": \"/dev/sda1\", \"State\": \"attached\", \"AttachTime\": \"2026-10-07T15:29:06+00:00\"}], \"Encrypted\": true, \"KmsKeyId\": \"arn:aws:kms:ap-southeast-2:803656589923:key/1ad9e0e5-ad7c-4f52-8b41-50c266898626\"}]}, \"warning\": null, \"api_calls\": [{\"service\": \"ec2\", \"operation\": \"DescribeVolumes\", \"status\": \"success\", \"n_items\": {\"Volumes\": 2}}]}"
        }
      ],
      "structuredContent": {
        "status": "success",
        "stdout": "",
        "return_value": {
          "Volumes": [
            {
              "AvailabilityZoneId": "apse2-az1",
              "Iops": 3000,
              "Tags": [
                {
                  "Key": "Name",
                  "Value": "p85-continuation-v1"
                },
                {
                  "Key": "research.stage",
                  "Value": "8.5"
                },
                {
                  "Key": "research.package",
                  "Value": "phase85-continuation-v1"
                },
                {
                  "Key": "research.owner",
                  "Value": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                }
              ],
              "VolumeType": "gp3",
              "MultiAttachEnabled": false,
              "Throughput": 125,
              "Operator": {
                "Managed": false,
                "HiddenByDefault": false
              },
              "VolumeArn": "arn:aws:ec2:ap-southeast-2:803656589923:volume/vol-0f667d76019af7a47",
              "OwnerId": "803656589923",
              "VolumeId": "vol-0f667d76019af7a47",
              "Size": 160,
              "SnapshotId": "snap-04f8536d791ceaecf",
              "AvailabilityZone": "ap-southeast-2a",
              "State": "in-use",
              "CreateTime": "2026-10-07T20:26:10.176000+00:00",
              "Attachments": [
                {
                  "DeleteOnTermination": false,
                  "EbsCardIndex": 0,
                  "VolumeId": "vol-0f667d76019af7a47",
                  "InstanceId": "i-034252c3e9b083abf",
                  "Device": "/dev/sda1",
                  "State": "attached",
                  "AttachTime": "2026-10-07T20:26:10+00:00"
                }
              ],
              "Encrypted": true,
              "KmsKeyId": "arn:aws:kms:ap-southeast-2:803656589923:key/1ad9e0e5-ad7c-4f52-8b41-50c266898626"
            },
            {
              "AvailabilityZoneId": "apse2-az1",
              "Iops": 3000,
              "Tags": [
                {
                  "Key": "Name",
                  "Value": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                },
                {
                  "Key": "research.owner",
                  "Value": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                },
                {
                  "Key": "research.stage",
                  "Value": "8.5"
                }
              ],
              "VolumeType": "gp3",
              "MultiAttachEnabled": false,
              "Throughput": 125,
              "Operator": {
                "Managed": false,
                "HiddenByDefault": false
              },
              "VolumeArn": "arn:aws:ec2:ap-southeast-2:803656589923:volume/vol-07baf9132bce08e77",
              "OwnerId": "803656589923",
              "VolumeId": "vol-07baf9132bce08e77",
              "Size": 160,
              "SnapshotId": "snap-04f8536d791ceaecf",
              "AvailabilityZone": "ap-southeast-2a",
              "State": "in-use",
              "CreateTime": "2026-10-07T15:29:06.157000+00:00",
              "Attachments": [
                {
                  "DeleteOnTermination": false,
                  "EbsCardIndex": 0,
                  "VolumeId": "vol-07baf9132bce08e77",
                  "InstanceId": "i-0a6196aff6f8098ac",
                  "Device": "/dev/sda1",
                  "State": "attached",
                  "AttachTime": "2026-10-07T15:29:06+00:00"
                }
              ],
              "Encrypted": true,
              "KmsKeyId": "arn:aws:kms:ap-southeast-2:803656589923:key/1ad9e0e5-ad7c-4f52-8b41-50c266898626"
            }
          ]
        },
        "api_calls": [
          {
            "service": "ec2",
            "operation": "DescribeVolumes",
            "status": "success",
            "n_items": {
              "Volumes": 2
            }
          }
        ]
      },
      "isError": false
    }
  },
  "old-host-cleanup-termination.json": {
    "sha256": "37935488f0dd67ed74b0b747c1f6ac772889a761399c69d5f16c8c6a70350f00",
    "result": {
      "content": [
        {
          "type": "text",
          "text": "{\"status\": \"success\", \"stdout\": \"\", \"stderr\": null, \"return_value\": {\"verified_original\": {\"Reservations\": [{\"ReservationId\": \"r-09dd2a8d6fada358a\", \"OwnerId\": \"803656589923\", \"Groups\": [], \"Instances\": [{\"Architecture\": \"x86_64\", \"BlockDeviceMappings\": [{\"DeviceName\": \"/dev/sda1\", \"Ebs\": {\"AttachTime\": \"2026-10-07T15:29:06+00:00\", \"DeleteOnTermination\": false, \"Status\": \"attached\", \"VolumeId\": \"vol-07baf9132bce08e77\", \"EbsCardIndex\": 0}}], \"ClientToken\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\", \"EbsOptimized\": false, \"EnaSupport\": true, \"Hypervisor\": \"xen\", \"IamInstanceProfile\": {\"Arn\": \"arn:aws:iam::803656589923:instance-profile/FYP-p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\", \"Id\": \"AIPA3WHNKMJRVRF7W6G3I\"}, \"NetworkInterfaces\": [{\"Attachment\": {\"AttachTime\": \"2026-10-07T15:29:05+00:00\", \"AttachmentId\": \"eni-attach-0813fcecf35d7cf54\", \"DeleteOnTermination\": true, \"DeviceIndex\": 0, \"Status\": \"attached\", \"NetworkCardIndex\": 0}, \"Description\": \"\", \"Groups\": [{\"GroupId\": \"sg-076d87ac5db0a6f52\", \"GroupName\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}], \"Ipv6Addresses\": [], \"MacAddress\": \"02:ff:c8:a3:48:07\", \"NetworkInterfaceId\": \"eni-0b2d2e6ce97e47a2f\", \"OwnerId\": \"803656589923\", \"PrivateDnsName\": \"ip-172-31-4-109.ap-southeast-2.compute.internal\", \"PrivateIpAddress\": \"172.31.4.109\", \"PrivateIpAddresses\": [{\"Primary\": true, \"PrivateDnsName\": \"ip-172-31-4-109.ap-southeast-2.compute.internal\", \"PrivateIpAddress\": \"172.31.4.109\"}], \"SourceDestCheck\": true, \"Status\": \"in-use\", \"SubnetId\": \"subnet-05c5c729c83dc651b\", \"VpcId\": \"vpc-0c74e59331cbc1caa\", \"InterfaceType\": \"interface\", \"Operator\": {\"Managed\": false}}], \"RootDeviceName\": \"/dev/sda1\", \"RootDeviceType\": \"ebs\", \"SecurityGroups\": [{\"GroupId\": \"sg-076d87ac5db0a6f52\", \"GroupName\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}], \"SourceDestCheck\": true, \"StateReason\": {\"Code\": \"Client.UserInitiatedShutdown\", \"Message\": \"Client.UserInitiatedShutdown: User initiated shutdown\"}, \"Tags\": [{\"Key\": \"research.owner\", \"Value\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}, {\"Key\": \"Name\", \"Value\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}, {\"Key\": \"research.stage\", \"Value\": \"8.5\"}], \"VirtualizationType\": \"hvm\", \"CpuOptions\": {\"CoreCount\": 1, \"ThreadsPerCore\": 2}, \"CapacityReservationSpecification\": {\"CapacityReservationPreference\": \"open\"}, \"HibernationOptions\": {\"Configured\": false}, \"MetadataOptions\": {\"State\": \"applied\", \"HttpTokens\": \"required\", \"HttpPutResponseHopLimit\": 1, \"HttpEndpoint\": \"enabled\", \"HttpProtocolIpv6\": \"disabled\", \"InstanceMetadataTags\": \"disabled\"}, \"EnclaveOptions\": {\"Enabled\": false}, \"BootMode\": \"uefi-preferred\", \"PlatformDetails\": \"Linux/UNIX\", \"UsageOperation\": \"RunInstances\", \"UsageOperationUpdateTime\": \"2026-10-07T15:29:05+00:00\", \"PrivateDnsNameOptions\": {\"HostnameType\": \"ip-name\", \"EnableResourceNameDnsARecord\": false, \"EnableResourceNameDnsAAAARecord\": false}, \"MaintenanceOptions\": {\"AutoRecovery\": \"default\", \"RebootMigration\": \"default\"}, \"CurrentInstanceBootMode\": \"uefi\", \"NetworkPerformanceOptions\": {\"BandwidthWeighting\": \"default\"}, \"Operator\": {\"Managed\": false, \"HiddenByDefault\": false}, \"InstanceId\": \"i-0a6196aff6f8098ac\", \"ImageId\": \"ami-090b1140798d2d006\", \"State\": {\"Code\": 80, \"Name\": \"stopped\"}, \"PrivateDnsName\": \"ip-172-31-4-109.ap-southeast-2.compute.internal\", \"PublicDnsName\": \"\", \"StateTransitionReason\": \"User initiated (2026-10-07 15:57:46 GMT)\", \"AmiLaunchIndex\": 0, \"ProductCodes\": [], \"InstanceType\": \"m7i-flex.large\", \"LaunchTime\": \"2026-10-07T15:29:05+00:00\", \"Placement\": {\"AvailabilityZoneId\": \"apse2-az1\", \"GroupName\": \"\", \"Tenancy\": \"default\", \"AvailabilityZone\": \"ap-southeast-2a\"}, \"Monitoring\": {\"State\": \"disabled\"}, \"SubnetId\": \"subnet-05c5c729c83dc651b\", \"VpcId\": \"vpc-0c74e59331cbc1caa\", \"PrivateIpAddress\": \"172.31.4.109\"}]}]}, \"verified_root\": {\"Volumes\": [{\"AvailabilityZoneId\": \"apse2-az1\", \"Iops\": 3000, \"Tags\": [{\"Key\": \"Name\", \"Value\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}, {\"Key\": \"research.owner\", \"Value\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}, {\"Key\": \"research.stage\", \"Value\": \"8.5\"}], \"VolumeType\": \"gp3\", \"MultiAttachEnabled\": false, \"Throughput\": 125, \"Operator\": {\"Managed\": false, \"HiddenByDefault\": false}, \"VolumeArn\": \"arn:aws:ec2:ap-southeast-2:803656589923:volume/vol-07baf9132bce08e77\", \"OwnerId\": \"803656589923\", \"VolumeId\": \"vol-07baf9132bce08e77\", \"Size\": 160, \"SnapshotId\": \"snap-04f8536d791ceaecf\", \"AvailabilityZone\": \"ap-southeast-2a\", \"State\": \"in-use\", \"CreateTime\": \"2026-10-07T15:29:06.157000+00:00\", \"Attachments\": [{\"DeleteOnTermination\": false, \"EbsCardIndex\": 0, \"VolumeId\": \"vol-07baf9132bce08e77\", \"InstanceId\": \"i-0a6196aff6f8098ac\", \"Device\": \"/dev/sda1\", \"State\": \"attached\", \"AttachTime\": \"2026-10-07T15:29:06+00:00\"}], \"Encrypted\": true, \"KmsKeyId\": \"arn:aws:kms:ap-southeast-2:803656589923:key/1ad9e0e5-ad7c-4f52-8b41-50c266898626\"}]}, \"termination\": {\"TerminatingInstances\": [{\"InstanceId\": \"i-0a6196aff6f8098ac\", \"CurrentState\": {\"Code\": 48, \"Name\": \"terminated\"}, \"PreviousState\": {\"Code\": 80, \"Name\": \"stopped\"}}]}, \"retained_disk_delete_pending\": true, \"s3_deleted\": false, \"local_deleted\": false}, \"warning\": null, \"api_calls\": [{\"service\": \"ec2\", \"operation\": \"DescribeInstances\", \"status\": \"success\", \"n_items\": {\"Reservations\": 1}}, {\"service\": \"ec2\", \"operation\": \"DescribeVolumes\", \"status\": \"success\", \"n_items\": {\"Volumes\": 1}}, {\"service\": \"ec2\", \"operation\": \"TerminateInstances\", \"status\": \"success\", \"n_items\": {\"TerminatingInstances\": 1}}]}"
        }
      ],
      "structuredContent": {
        "status": "success",
        "stdout": "",
        "return_value": {
          "verified_original": {
            "Reservations": [
              {
                "ReservationId": "r-09dd2a8d6fada358a",
                "OwnerId": "803656589923",
                "Groups": [],
                "Instances": [
                  {
                    "Architecture": "x86_64",
                    "BlockDeviceMappings": [
                      {
                        "DeviceName": "/dev/sda1",
                        "Ebs": {
                          "AttachTime": "2026-10-07T15:29:06+00:00",
                          "DeleteOnTermination": false,
                          "Status": "attached",
                          "VolumeId": "vol-07baf9132bce08e77",
                          "EbsCardIndex": 0
                        }
                      }
                    ],
                    "ClientToken": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9",
                    "EbsOptimized": false,
                    "EnaSupport": true,
                    "Hypervisor": "xen",
                    "IamInstanceProfile": {
                      "Arn": "arn:aws:iam::803656589923:instance-profile/FYP-p85-01a116f7-3b82-7a79-8653-3aee62dc99e9",
                      "Id": "AIPA3WHNKMJRVRF7W6G3I"
                    },
                    "NetworkInterfaces": [
                      {
                        "Attachment": {
                          "AttachTime": "2026-10-07T15:29:05+00:00",
                          "AttachmentId": "eni-attach-0813fcecf35d7cf54",
                          "DeleteOnTermination": true,
                          "DeviceIndex": 0,
                          "Status": "attached",
                          "NetworkCardIndex": 0
                        },
                        "Description": "",
                        "Groups": [
                          {
                            "GroupId": "sg-076d87ac5db0a6f52",
                            "GroupName": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                          }
                        ],
                        "Ipv6Addresses": [],
                        "MacAddress": "02:ff:c8:a3:48:07",
                        "NetworkInterfaceId": "eni-0b2d2e6ce97e47a2f",
                        "OwnerId": "803656589923",
                        "PrivateDnsName": "ip-172-31-4-109.ap-southeast-2.compute.internal",
                        "PrivateIpAddress": "172.31.4.109",
                        "PrivateIpAddresses": [
                          {
                            "Primary": true,
                            "PrivateDnsName": "ip-172-31-4-109.ap-southeast-2.compute.internal",
                            "PrivateIpAddress": "172.31.4.109"
                          }
                        ],
                        "SourceDestCheck": true,
                        "Status": "in-use",
                        "SubnetId": "subnet-05c5c729c83dc651b",
                        "VpcId": "vpc-0c74e59331cbc1caa",
                        "InterfaceType": "interface",
                        "Operator": {
                          "Managed": false
                        }
                      }
                    ],
                    "RootDeviceName": "/dev/sda1",
                    "RootDeviceType": "ebs",
                    "SecurityGroups": [
                      {
                        "GroupId": "sg-076d87ac5db0a6f52",
                        "GroupName": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                      }
                    ],
                    "SourceDestCheck": true,
                    "StateReason": {
                      "Code": "Client.UserInitiatedShutdown",
                      "Message": "Client.UserInitiatedShutdown: User initiated shutdown"
                    },
                    "Tags": [
                      {
                        "Key": "research.owner",
                        "Value": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                      },
                      {
                        "Key": "Name",
                        "Value": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                      },
                      {
                        "Key": "research.stage",
                        "Value": "8.5"
                      }
                    ],
                    "VirtualizationType": "hvm",
                    "CpuOptions": {
                      "CoreCount": 1,
                      "ThreadsPerCore": 2
                    },
                    "CapacityReservationSpecification": {
                      "CapacityReservationPreference": "open"
                    },
                    "HibernationOptions": {
                      "Configured": false
                    },
                    "MetadataOptions": {
                      "State": "applied",
                      "HttpTokens": "required",
                      "HttpPutResponseHopLimit": 1,
                      "HttpEndpoint": "enabled",
                      "HttpProtocolIpv6": "disabled",
                      "InstanceMetadataTags": "disabled"
                    },
                    "EnclaveOptions": {
                      "Enabled": false
                    },
                    "BootMode": "uefi-preferred",
                    "PlatformDetails": "Linux/UNIX",
                    "UsageOperation": "RunInstances",
                    "UsageOperationUpdateTime": "2026-10-07T15:29:05+00:00",
                    "PrivateDnsNameOptions": {
                      "HostnameType": "ip-name",
                      "EnableResourceNameDnsARecord": false,
                      "EnableResourceNameDnsAAAARecord": false
                    },
                    "MaintenanceOptions": {
                      "AutoRecovery": "default",
                      "RebootMigration": "default"
                    },
                    "CurrentInstanceBootMode": "uefi",
                    "NetworkPerformanceOptions": {
                      "BandwidthWeighting": "default"
                    },
                    "Operator": {
                      "Managed": false,
                      "HiddenByDefault": false
                    },
                    "InstanceId": "i-0a6196aff6f8098ac",
                    "ImageId": "ami-090b1140798d2d006",
                    "State": {
                      "Code": 80,
                      "Name": "stopped"
                    },
                    "PrivateDnsName": "ip-172-31-4-109.ap-southeast-2.compute.internal",
                    "PublicDnsName": "",
                    "StateTransitionReason": "User initiated (2026-10-07 15:57:46 GMT)",
                    "AmiLaunchIndex": 0,
                    "ProductCodes": [],
                    "InstanceType": "m7i-flex.large",
                    "LaunchTime": "2026-10-07T15:29:05+00:00",
                    "Placement": {
                      "AvailabilityZoneId": "apse2-az1",
                      "GroupName": "",
                      "Tenancy": "default",
                      "AvailabilityZone": "ap-southeast-2a"
                    },
                    "Monitoring": {
                      "State": "disabled"
                    },
                    "SubnetId": "subnet-05c5c729c83dc651b",
                    "VpcId": "vpc-0c74e59331cbc1caa",
                    "PrivateIpAddress": "172.31.4.109"
                  }
                ]
              }
            ]
          },
          "verified_root": {
            "Volumes": [
              {
                "AvailabilityZoneId": "apse2-az1",
                "Iops": 3000,
                "Tags": [
                  {
                    "Key": "Name",
                    "Value": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                  },
                  {
                    "Key": "research.owner",
                    "Value": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                  },
                  {
                    "Key": "research.stage",
                    "Value": "8.5"
                  }
                ],
                "VolumeType": "gp3",
                "MultiAttachEnabled": false,
                "Throughput": 125,
                "Operator": {
                  "Managed": false,
                  "HiddenByDefault": false
                },
                "VolumeArn": "arn:aws:ec2:ap-southeast-2:803656589923:volume/vol-07baf9132bce08e77",
                "OwnerId": "803656589923",
                "VolumeId": "vol-07baf9132bce08e77",
                "Size": 160,
                "SnapshotId": "snap-04f8536d791ceaecf",
                "AvailabilityZone": "ap-southeast-2a",
                "State": "in-use",
                "CreateTime": "2026-10-07T15:29:06.157000+00:00",
                "Attachments": [
                  {
                    "DeleteOnTermination": false,
                    "EbsCardIndex": 0,
                    "VolumeId": "vol-07baf9132bce08e77",
                    "InstanceId": "i-0a6196aff6f8098ac",
                    "Device": "/dev/sda1",
                    "State": "attached",
                    "AttachTime": "2026-10-07T15:29:06+00:00"
                  }
                ],
                "Encrypted": true,
                "KmsKeyId": "arn:aws:kms:ap-southeast-2:803656589923:key/1ad9e0e5-ad7c-4f52-8b41-50c266898626"
              }
            ]
          },
          "termination": {
            "TerminatingInstances": [
              {
                "InstanceId": "i-0a6196aff6f8098ac",
                "CurrentState": {
                  "Code": 48,
                  "Name": "terminated"
                },
                "PreviousState": {
                  "Code": 80,
                  "Name": "stopped"
                }
              }
            ]
          },
          "retained_disk_delete_pending": true,
          "s3_deleted": false,
          "local_deleted": false
        },
        "api_calls": [
          {
            "service": "ec2",
            "operation": "DescribeInstances",
            "status": "success",
            "n_items": {
              "Reservations": 1
            }
          },
          {
            "service": "ec2",
            "operation": "DescribeVolumes",
            "status": "success",
            "n_items": {
              "Volumes": 1
            }
          },
          {
            "service": "ec2",
            "operation": "TerminateInstances",
            "status": "success",
            "n_items": {
              "TerminatingInstances": 1
            }
          }
        ]
      },
      "isError": false
    }
  },
  "old-root-cleanup-delete.json": {
    "sha256": "bab7504d534ead6f9ff9e056277a317f4593a5258d1436da8dee89b682197c6c",
    "result": {
      "content": [
        {
          "type": "text",
          "text": "{\"status\": \"success\", \"stdout\": \"\", \"stderr\": null, \"return_value\": {\"verified_volume\": {\"Volumes\": [{\"AvailabilityZoneId\": \"apse2-az1\", \"Iops\": 3000, \"Tags\": [{\"Key\": \"Name\", \"Value\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}, {\"Key\": \"research.owner\", \"Value\": \"p85-01a116f7-3b82-7a79-8653-3aee62dc99e9\"}, {\"Key\": \"research.stage\", \"Value\": \"8.5\"}], \"VolumeType\": \"gp3\", \"MultiAttachEnabled\": false, \"Throughput\": 125, \"Operator\": {\"Managed\": false, \"HiddenByDefault\": false}, \"VolumeArn\": \"arn:aws:ec2:ap-southeast-2:803656589923:volume/vol-07baf9132bce08e77\", \"OwnerId\": \"803656589923\", \"VolumeId\": \"vol-07baf9132bce08e77\", \"Size\": 160, \"SnapshotId\": \"snap-04f8536d791ceaecf\", \"AvailabilityZone\": \"ap-southeast-2a\", \"State\": \"available\", \"CreateTime\": \"2026-10-07T15:29:06.157000+00:00\", \"Attachments\": [], \"Encrypted\": true, \"KmsKeyId\": \"arn:aws:kms:ap-southeast-2:803656589923:key/1ad9e0e5-ad7c-4f52-8b41-50c266898626\"}]}, \"delete\": {}, \"removed_only\": \"vol-07baf9132bce08e77\", \"s3_deleted\": false, \"local_deleted\": false}, \"warning\": null, \"api_calls\": [{\"service\": \"ec2\", \"operation\": \"DescribeVolumes\", \"status\": \"success\", \"n_items\": {\"Volumes\": 1}}, {\"service\": \"ec2\", \"operation\": \"DeleteVolume\", \"status\": \"success\"}]}"
        }
      ],
      "structuredContent": {
        "status": "success",
        "stdout": "",
        "return_value": {
          "verified_volume": {
            "Volumes": [
              {
                "AvailabilityZoneId": "apse2-az1",
                "Iops": 3000,
                "Tags": [
                  {
                    "Key": "Name",
                    "Value": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                  },
                  {
                    "Key": "research.owner",
                    "Value": "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
                  },
                  {
                    "Key": "research.stage",
                    "Value": "8.5"
                  }
                ],
                "VolumeType": "gp3",
                "MultiAttachEnabled": false,
                "Throughput": 125,
                "Operator": {
                  "Managed": false,
                  "HiddenByDefault": false
                },
                "VolumeArn": "arn:aws:ec2:ap-southeast-2:803656589923:volume/vol-07baf9132bce08e77",
                "OwnerId": "803656589923",
                "VolumeId": "vol-07baf9132bce08e77",
                "Size": 160,
                "SnapshotId": "snap-04f8536d791ceaecf",
                "AvailabilityZone": "ap-southeast-2a",
                "State": "available",
                "CreateTime": "2026-10-07T15:29:06.157000+00:00",
                "Attachments": [],
                "Encrypted": true,
                "KmsKeyId": "arn:aws:kms:ap-southeast-2:803656589923:key/1ad9e0e5-ad7c-4f52-8b41-50c266898626"
              }
            ]
          },
          "delete": {},
          "removed_only": "vol-07baf9132bce08e77",
          "s3_deleted": false,
          "local_deleted": false
        },
        "api_calls": [
          {
            "service": "ec2",
            "operation": "DescribeVolumes",
            "status": "success",
            "n_items": {
              "Volumes": 1
            }
          },
          {
            "service": "ec2",
            "operation": "DeleteVolume",
            "status": "success"
          }
        ]
      },
      "isError": false
    }
  },
  "health-finalize-result.json": {
    "sha256": "9d44353263ad1451338e44e2c59fc82b384d484b48e2e30aeaedd0a3bae4e947",
    "result": {
      "content": [
        {
          "type": "text",
          "text": "{\"status\": \"success\", \"stdout\": \"\", \"stderr\": null, \"return_value\": {\"CommandId\": \"fe17fc92-b000-45a4-a7a4-d7f0e640b3d8\", \"InstanceId\": \"i-034252c3e9b083abf\", \"Comment\": \"Verify retained diagnostic health and now-free ports; no replay or main driver\", \"DocumentName\": \"AWS-RunShellScript\", \"DocumentVersion\": \"$DEFAULT\", \"PluginName\": \"aws:runShellScript\", \"ResponseCode\": 0, \"ExecutionStartDateTime\": \"2026-10-07T20:42:12.775Z\", \"ExecutionElapsedTime\": \"PT2.92S\", \"ExecutionEndDateTime\": \"2026-10-07T20:42:14.775Z\", \"Status\": \"Success\", \"StatusDetails\": \"Success\", \"StandardOutputContent\": \"{\\\"status\\\": \\\"PASS\\\", \\\"source_files\\\": 1903, \\\"available_memory_bytes\\\": 7340748800, \\\"disk_free_bytes\\\": 160552390656, \\\"dependency_record_hashes_verified\\\": 13629, \\\"health\\\": {\\\"api\\\": {\\\"status\\\": 200, \\\"evidence\\\": \\\"retained service HTTP access log\\\", \\\"response_body_retained\\\": false, \\\"log_sha256\\\": \\\"db45afe1e8ac4acb19398a555ea343469c8d3079f206d63130c95405f6b3762b\\\"}, \\\"voice\\\": {\\\"status\\\": 200, \\\"evidence\\\": \\\"retained service HTTP access log\\\", \\\"response_body_retained\\\": false, \\\"log_sha256\\\": \\\"ec92c133c7eae81860575b82c9d11921a46aca776fc8a7001e7c3d688210c72e\\\"}, \\\"worker\\\": {\\\"status\\\": 200, \\\"evidence\\\": \\\"retained service HTTP access log\\\", \\\"response_body_retained\\\": false, \\\"log_sha256\\\": \\\"8c3b2658ae9e803e6cdbcd878fb0427df2578df0dd81ece0c8a37f14a85fd782\\\"}, \\\"simulator\\\": {\\\"status\\\": 200, \\\"evidence\\\": \\\"retained service HTTP access log\\\", \\\"response_body_retained\\\": false, \\\"log_sha256\\\": \\\"bed1a3ae7c69da224fd34edb03d61c1b75ee905f992c6a1900070c241f3d53fb\\\"}}, \\\"driver_calls\\\": 0}\\nactive\\nactive\\nNEXT                                  LEFT LAST PASSED UNIT                                        ACTIVATES\\nWed 2026-10-07 22:26:52 UTC       1h 44min -         - fyp-p85-continuation-preparation-stop.timer fyp-p85-continuation-bootstrap-stop.service\\nThu 2026-10-22 15:24:23 UTC 2 weeks 0 days -         - fyp-p85-continuation-bootstrap-stop.timer   fyp-p85-continuation-bootstrap-stop.service\\n\\n2 timers listed.\\nPass --all to see loaded but inactive timers, too.\\n\", \"StandardOutputUrl\": \"\", \"StandardErrorContent\": \"\", \"StandardErrorUrl\": \"\", \"CloudWatchOutputConfig\": {\"CloudWatchLogGroupName\": \"\", \"CloudWatchOutputEnabled\": false}}, \"warning\": null, \"api_calls\": [{\"service\": \"ssm\", \"operation\": \"GetCommandInvocation\", \"status\": \"success\"}]}"
        }
      ],
      "structuredContent": {
        "status": "success",
        "stdout": "",
        "return_value": {
          "CommandId": "fe17fc92-b000-45a4-a7a4-d7f0e640b3d8",
          "InstanceId": "i-034252c3e9b083abf",
          "Comment": "Verify retained diagnostic health and now-free ports; no replay or main driver",
          "DocumentName": "AWS-RunShellScript",
          "DocumentVersion": "$DEFAULT",
          "PluginName": "aws:runShellScript",
          "ResponseCode": 0,
          "ExecutionStartDateTime": "2026-10-07T20:42:12.775Z",
          "ExecutionElapsedTime": "PT2.92S",
          "ExecutionEndDateTime": "2026-10-07T20:42:14.775Z",
          "Status": "Success",
          "StatusDetails": "Success",
          "StandardOutputContent": "{\"status\": \"PASS\", \"source_files\": 1903, \"available_memory_bytes\": 7340748800, \"disk_free_bytes\": 160552390656, \"dependency_record_hashes_verified\": 13629, \"health\": {\"api\": {\"status\": 200, \"evidence\": \"retained service HTTP access log\", \"response_body_retained\": false, \"log_sha256\": \"db45afe1e8ac4acb19398a555ea343469c8d3079f206d63130c95405f6b3762b\"}, \"voice\": {\"status\": 200, \"evidence\": \"retained service HTTP access log\", \"response_body_retained\": false, \"log_sha256\": \"ec92c133c7eae81860575b82c9d11921a46aca776fc8a7001e7c3d688210c72e\"}, \"worker\": {\"status\": 200, \"evidence\": \"retained service HTTP access log\", \"response_body_retained\": false, \"log_sha256\": \"8c3b2658ae9e803e6cdbcd878fb0427df2578df0dd81ece0c8a37f14a85fd782\"}, \"simulator\": {\"status\": 200, \"evidence\": \"retained service HTTP access log\", \"response_body_retained\": false, \"log_sha256\": \"bed1a3ae7c69da224fd34edb03d61c1b75ee905f992c6a1900070c241f3d53fb\"}}, \"driver_calls\": 0}\nactive\nactive\nNEXT                                  LEFT LAST PASSED UNIT                                        ACTIVATES\nWed 2026-10-07 22:26:52 UTC       1h 44min -         - fyp-p85-continuation-preparation-stop.timer fyp-p85-continuation-bootstrap-stop.service\nThu 2026-10-22 15:24:23 UTC 2 weeks 0 days -         - fyp-p85-continuation-bootstrap-stop.timer   fyp-p85-continuation-bootstrap-stop.service\n\n2 timers listed.\nPass --all to see loaded but inactive timers, too.\n",
          "StandardOutputUrl": "",
          "StandardErrorContent": "",
          "StandardErrorUrl": "",
          "CloudWatchOutputConfig": {
            "CloudWatchLogGroupName": "",
            "CloudWatchOutputEnabled": false
          }
        },
        "api_calls": [
          {
            "service": "ssm",
            "operation": "GetCommandInvocation",
            "status": "success"
          }
        ]
      },
      "isError": false
    }
  },
  "socket-inspection-result.json": {
    "sha256": "d72c796c6020db6c15484da12402a2de5b80cf4b53b0a740306c8c56887cc551",
    "result": {
      "content": [
        {
          "type": "text",
          "text": "{\"status\": \"success\", \"stdout\": \"\", \"stderr\": null, \"return_value\": {\"CommandId\": \"16442521-77b5-498e-b3ce-ba1ee6552b0f\", \"InstanceId\": \"i-034252c3e9b083abf\", \"Comment\": \"Inspect closed diagnostic ports and retained evidence; no driver\", \"DocumentName\": \"AWS-RunShellScript\", \"DocumentVersion\": \"$DEFAULT\", \"PluginName\": \"aws:runShellScript\", \"ResponseCode\": 0, \"ExecutionStartDateTime\": \"2026-10-07T20:40:47.645Z\", \"ExecutionElapsedTime\": \"PT0.054S\", \"ExecutionEndDateTime\": \"2026-10-07T20:40:47.645Z\", \"Status\": \"Success\", \"StatusDetails\": \"Success\", \"StandardOutputContent\": \"2026-10-07T20:40:47+00:00\\nState  Recv-Q Send-Q Local Address:Port  Peer Address:PortProcess                                    \\nLISTEN 0      4096   127.0.0.53%lo:53         0.0.0.0:*    users:((\\\"systemd-resolve\\\",pid=2370,fd=15))\\nLISTEN 0      4096      127.0.0.54:53         0.0.0.0:*    users:((\\\"systemd-resolve\\\",pid=2370,fd=17))\\nLISTEN 0      4096       127.0.0.1:35083      0.0.0.0:*    users:((\\\"containerd\\\",pid=1846,fd=14))     \\nLISTEN 0      4096         0.0.0.0:22         0.0.0.0:*    users:((\\\"systemd\\\",pid=1,fd=237))          \\nLISTEN 0      4096            [::]:22            [::]:*    users:((\\\"systemd\\\",pid=1,fd=243))          \\nfyp-continuation-uv-tool Created\\nINFO  [alembic.runtime.migration] Running upgrade 0008_phase6_research -> 0009_phase6_baselines, Persist raw and normalized provider observations for research baselines.\\nINFO  [alembic.runtime.migration] Running upgrade 0009_phase6_baselines -> 0010_phase6_research_arm, Pin an explicit repair ablation arm on synthetic experiment workflows.\\nINFO  [alembic.runtime.migration] Running upgrade 0010_phase6_research_arm -> 0011_phase6_b3_audio, Confine permitless decisive audio to explicitly tagged B3 experiments.\\nINFO  [alembic.runtime.migration] Running upgrade 0011_phase6_b3_audio -> 0012_readiness_repair, Durable repair delivery leases; previous migrations stay unchanged.\\nINFO  [alembic.runtime.migration] Running upgrade 0012_readiness_repair -> 0013_readiness_capability, Enforce ablated repair capability at the durable database boundary.\\n700 /var/lib/fyp-owner\\n600 /var/lib/fyp-owner/owner.key\\nactive\\nactive\\n\", \"StandardOutputUrl\": \"\", \"StandardErrorContent\": \"\", \"StandardErrorUrl\": \"\", \"CloudWatchOutputConfig\": {\"CloudWatchLogGroupName\": \"\", \"CloudWatchOutputEnabled\": false}}, \"warning\": null, \"api_calls\": [{\"service\": \"ssm\", \"operation\": \"GetCommandInvocation\", \"status\": \"success\"}]}"
        }
      ],
      "structuredContent": {
        "status": "success",
        "stdout": "",
        "return_value": {
          "CommandId": "16442521-77b5-498e-b3ce-ba1ee6552b0f",
          "InstanceId": "i-034252c3e9b083abf",
          "Comment": "Inspect closed diagnostic ports and retained evidence; no driver",
          "DocumentName": "AWS-RunShellScript",
          "DocumentVersion": "$DEFAULT",
          "PluginName": "aws:runShellScript",
          "ResponseCode": 0,
          "ExecutionStartDateTime": "2026-10-07T20:40:47.645Z",
          "ExecutionElapsedTime": "PT0.054S",
          "ExecutionEndDateTime": "2026-10-07T20:40:47.645Z",
          "Status": "Success",
          "StatusDetails": "Success",
          "StandardOutputContent": "2026-10-07T20:40:47+00:00\nState  Recv-Q Send-Q Local Address:Port  Peer Address:PortProcess                                    \nLISTEN 0      4096   127.0.0.53%lo:53         0.0.0.0:*    users:((\"systemd-resolve\",pid=2370,fd=15))\nLISTEN 0      4096      127.0.0.54:53         0.0.0.0:*    users:((\"systemd-resolve\",pid=2370,fd=17))\nLISTEN 0      4096       127.0.0.1:35083      0.0.0.0:*    users:((\"containerd\",pid=1846,fd=14))     \nLISTEN 0      4096         0.0.0.0:22         0.0.0.0:*    users:((\"systemd\",pid=1,fd=237))          \nLISTEN 0      4096            [::]:22            [::]:*    users:((\"systemd\",pid=1,fd=243))          \nfyp-continuation-uv-tool Created\nINFO  [alembic.runtime.migration] Running upgrade 0008_phase6_research -> 0009_phase6_baselines, Persist raw and normalized provider observations for research baselines.\nINFO  [alembic.runtime.migration] Running upgrade 0009_phase6_baselines -> 0010_phase6_research_arm, Pin an explicit repair ablation arm on synthetic experiment workflows.\nINFO  [alembic.runtime.migration] Running upgrade 0010_phase6_research_arm -> 0011_phase6_b3_audio, Confine permitless decisive audio to explicitly tagged B3 experiments.\nINFO  [alembic.runtime.migration] Running upgrade 0011_phase6_b3_audio -> 0012_readiness_repair, Durable repair delivery leases; previous migrations stay unchanged.\nINFO  [alembic.runtime.migration] Running upgrade 0012_readiness_repair -> 0013_readiness_capability, Enforce ablated repair capability at the durable database boundary.\n700 /var/lib/fyp-owner\n600 /var/lib/fyp-owner/owner.key\nactive\nactive\n",
          "StandardOutputUrl": "",
          "StandardErrorContent": "",
          "StandardErrorUrl": "",
          "CloudWatchOutputConfig": {
            "CloudWatchLogGroupName": "",
            "CloudWatchOutputEnabled": false
          }
        },
        "api_calls": [
          {
            "service": "ssm",
            "operation": "GetCommandInvocation",
            "status": "success"
          }
        ]
      },
      "isError": false
    }
  }
}
EVIDENCE
cd /opt/fyp-phase8-continuation-v1
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
.venv/bin/python -B - <<'PY'
import hashlib,json,socket,subprocess,sys
from datetime import timedelta
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-continuation/v1'))
from controls import Journal,canonical,guard,hash_file,read,utc,write_new
from handover import CHECKS,ContinuationAuthority,closed_boundary,verify_imported_first,verify_members
from runner import verify_clock
from storage import ObjectProof,S3Cloud
from transport import Receipt,S3Store
from research.execution_linux_v1.platform import host
root=Path('/var/lib/p8-continuation/run');dep=Path('/var/lib/p8-continuation/deployment');owner=Path('/var/lib/fyp-owner')
external=read(dep/'external-readiness-evidence.json')
def aws_record(name):
 return json.loads(external[name]['result']['content'][0]['text'])
if aws_record('old-root-cleanup-delete.json')['status']!='success':raise ValueError('AUTHORIZED_OLD_ROOT_CLEANUP_NOT_VERIFIED')
if aws_record('old-host-cleanup-termination.json')['return_value']['termination']['TerminatingInstances'][0]['PreviousState']['Name']!='stopped':raise ValueError('ORIGINAL_HOST_NOT_STOPPED_BEFORE_CLEANUP')
credit=aws_record('preadmission-credits.json')['return_value']
if credit['accountPlanType']!='FREE' or credit['accountPlanStatus']!='ACTIVE' or credit['accountPlanRemainingCredits']['amount']<65:raise ValueError('PLAN_OR_CREDIT_GATE')
if read(dep/'host-health-readiness.json')['status']!='PASS':raise ValueError('ACTUAL_HOST_HEALTH_NOT_VERIFIED')
imported=read(dep/'import-and-backup-readiness.json')
if imported['status']!='PASS':raise ValueError('IMPORT_NOT_VERIFIED')
authority=ContinuationAuthority(root,read(root/'run.json'));freeze=authority.verify(prelaunch=True)
verify_imported_first(root);journal=Journal(root);journal.verify()
closed_boundary(journal.rows(),read(Path.cwd()/'artifacts/phase-8-review-freeze/v2/schedule.json')['rows']);verify_clock(root,authority.policy,utc())
if (root/'slots').exists() or read(root/'pause.json')['reason']!='CONTINUATION_REVIEW_REQUIRED':raise ValueError('PREMATURE_MAIN_OR_PAUSE_DRIFT')
policy=authority.policy;now=utc();finish=now+timedelta(hours=314)
cost=policy.committed_cost(finish+timedelta(minutes=30))
if finish>=policy.stop_at-timedelta(seconds=policy.admission_cutoff_seconds) or cost>=55:raise ValueError('CONSERVATIVE_REMAINING_PLAN_DOES_NOT_FIT')
backup=Path('/var/lib/p8-continuation/backup');cloud=S3Cloud(policy.cloud_bucket,f'exports/phase8/{policy.run_id}/');store=S3Store('fyp-research')
cloud_bytes=cloud.inventory()
with journal.connect() as db:outstanding=db.execute("SELECT COALESCE(sum(bytes),0) FROM reservations WHERE state!='VERIFIED'").fetchone()[0]
sample=host(root,backup);sample.update(working_bytes=0,backup_bytes=0)
guard(policy,sample,now,cloud_bytes+outstanding,extra_bytes=policy.slot_capacity_reserve_bytes)
if owner.stat().st_mode&0o777!=0o700 or (owner/'owner.key').stat().st_mode&0o777!=0o600:raise ValueError('OWNER_PERMISSIONS')
for port in (16432,16433,19100,19101,19102,19110):
 with socket.socket() as s:s.bind(('127.0.0.1',port))
if store.client.get_bucket_versioning(Bucket=policy.cloud_bucket).get('Status')!='Enabled':raise ValueError('VERSIONING_GATE')
for proof in imported['original_backups']+[imported['prelaunch_backup'],imported['permission_probe']]:
 store.head(Receipt.model_validate(proof))
verify_members(root.parent/'prelaunch-readback/x/slot')
for timer in ('fyp-p85-continuation-bootstrap-stop.timer','fyp-p85-continuation-preparation-stop.timer'):
 subprocess.run(['systemctl','is-active','--quiet',timer],check=True,timeout=10)
timers=subprocess.run(['systemctl','list-timers','fyp-p85-continuation-bootstrap-stop.timer','fyp-p85-continuation-preparation-stop.timer','--no-pager'],check=True,capture_output=True,text=True,timeout=10).stdout
if '2026-10-22 15:24:23' not in timers:raise ValueError('ABSOLUTE_DEADLINE_TIMER')
ready={
 'version':'phase85-continuation-v1','status':'PASS','at_utc':now.isoformat(),
 'instance_id':'i-034252c3e9b083abf','run_id':policy.run_id,
 'policy_sha256':hashlib.sha256(canonical(policy.model_dump(mode='json'))).hexdigest(),
 'handover_sha256':hash_file(root/'handover.json'),'boot_anchor_sha256':hash_file(root/'host-clock.json'),
 'checks':dict.fromkeys(CHECKS,True),
 'evidence':{'import_and_backups':hash_file(dep/'import-and-backup-readiness.json'),'hashes_and_empty_services':hash_file(dep/'host-health-readiness.json'),'external_API_records':hash_file(dep/'external-readiness-evidence.json'),'prelaunch_backup':imported['prelaunch_backup'],'permission_probe':imported['permission_probe'],'timers':timers,'source_and_freeze_chain':freeze},
 'original_host_disposition':'Verified STOPPED before authorized termination; original root deleted after independent evidence verification; never restarted',
 'budget':{'unchanged_total_usd':65,'unchanged_guard_usd':55,'reserve_inside_limits_usd':1.25,'conservative_13_day_plus_setup_cost_usd':cost,'projected_finish_utc':finish.isoformat()},
 'host':sample,'cloud_bytes_all_versions':cloud_bytes,'outstanding_bytes':outstanding,
 'original_deadline_utc':policy.stop_at.isoformat(),'operational_clock_reset':False,
 'first_raw_status':'FAILED','first_backed_up':1,'remaining_planned':1499,'main_driver_calls':0,
 'historical_readiness_failures_retained':True,
}
write_new(root/'continuation-readiness.json',ready)
journal.event('CONTINUATION_READINESS_VERIFIED',hash=hash_file(root/'continuation-readiness.json'),instance=ready['instance_id'],main_admitted=False)
print(json.dumps({'status':'PASS','readiness_sha256':hash_file(root/'continuation-readiness.json'),'instance_id':ready['instance_id'],'policy_sha256':ready['policy_sha256'],'handover_sha256':ready['handover_sha256'],'boot_anchor_sha256':ready['boot_anchor_sha256'],'checks':ready['checks'],'prelaunch_backup':imported['prelaunch_backup'],'conservative_cost_usd':cost,'main_admitted':False}))
PY
