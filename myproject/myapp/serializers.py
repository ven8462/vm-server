from rest_framework import serializers
from .models import VirtualMachine, SubUser, UserAssignedVM, Backup, Snapshot, Payment, SubscriptionPlan, UserSubscription, AuditLog, CustomUser, Role
from django.contrib.auth.models import Group
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.validators import EmailValidator
from rest_framework.validators import UniqueValidator



from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import CustomUser, Role

class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password']

    def validate_password(self, value):
        # Ensure that the password is hashed before saving
        return make_password(value)

    def create(self, validated_data):
        # Get the default role
        default_role = Role.get_default_role()
        # Create the user with the default role
        user = CustomUser.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=default_role
        )
        return user


class CustomUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(validators=[EmailValidator(message="Enter a valid email address.")])
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        user = CustomUser(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        user.set_password(validated_data['password'])  # Hash the password
        user.save()

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        return {
            'user': user,
            'token': str(refresh.access_token)  # Return access token only
        }
    


    
class VirtualMachineCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VirtualMachine
        fields = ['name', 'status', 'cpu', 'ram', 'cost']  

    def validate_status(self, value):
        if value not in ['running', 'stopped']:
            raise serializers.ValidationError("Status must be either 'running' or 'stopped'.")
        return value

    # def validate_cost(self, value):
    #     if value <= 0:
    #         raise serializers.ValidationError("Cost must be a positive value.")
    #     return value

    def validate(self, data):
        return data



class PaymentSerializer(serializers.ModelSerializer):
    backup_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Payment
        fields = ['card_number', 'amount', 'backup_id']

    def validate_backup_id(self, value):
        # Check if the backup exists
        try:
            backup = Backup.objects.get(id=value)
        except Backup.DoesNotExist:
            raise serializers.ValidationError("Backup with this ID does not exist.")
        return value

    def create(self, validated_data):
        # Retrieve backup and mark its status as paid
        backup = Backup.objects.get(id=validated_data['backup_id'])
        backup.status = 'paid'
        backup.save()

        # Remove backup_id from validated_data as it's not part of the Payment model
        validated_data.pop('backup_id')

        # Create and return the payment
        return Payment.objects.create(**validated_data)



class AssignVMMachineSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    vm_id = serializers.IntegerField()

    def validate(self, data):
        # Check if the user exists
        try:
            user = CustomUser.objects.get(pk=data['user_id'])
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")

        # Check if the VM exists
        try:
            vm = VirtualMachine.objects.get(pk=data['vm_id'])
        except VirtualMachine.DoesNotExist:
            raise serializers.ValidationError("Virtual Machine does not exist.")
        
        # Ensure that the user has fewer than 20 VMs assigned
        assigned_vm_count = UserAssignedVM.objects.filter(new_owner=user).count()
        if assigned_vm_count >= 20:
            raise serializers.ValidationError("This user already has the maximum allowed number of virtual machines assigned.")

        return data


class BackupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Backup
        fields = ['vm', 'size', 'bill']
    
    def validate_vm(self, value):
        """Check if the Virtual Machine exists."""
        if not VirtualMachine.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Virtual Machine does not exist.")
        return value

    def validate_size(self, value):
        """Ensure the size is a positive number."""
        if value <= 0:
            raise serializers.ValidationError("Size must be greater than zero.")
        return value

    def validate_bill(self, value):
        """Ensure the bill is a non-negative number."""
        if value < 0:
            raise serializers.ValidationError("Bill cannot be negative.")
        return value


class VirtualMachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = VirtualMachine
        fields = ['name', 'cpu', 'ram', 'cost', 'status'] 

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.cpu = validated_data.get('cpu', instance.cpu)
        instance.ram = validated_data.get('ram', instance.ram)
        instance.cost = validated_data.get('cost', instance.cost)
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance

class SubUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubUser
        fields = ['id', 'sub_username', 'assigned_model', 'created_at']


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role']


class VirtualMachineSerializers(serializers.ModelSerializer):
    class Meta:
        model = VirtualMachine
        fields = ['id', 'name', 'cpu', 'ram', 'cost', 'status', 'unbacked_data', 'created_at', 'updated_at']

class VirtualMachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = VirtualMachine
        fields = ['name', 'cpu', 'ram', 'cost', 'status', 'id',  'created_at', 'owner'] 



class VirtualMachineUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VirtualMachine
        fields = ['name', 'status'] 

    def validate_status(self, value):
        if value not in ['running', 'stopped']:
            raise serializers.ValidationError("Status must be either 'running' or 'stopped'.")
        return value


class BackupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Backup
        fields = ['vm', 'size']

    def validate_vm(self, value):
        if not VirtualMachine.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("The specified virtual machine does not exist.")
        return value

    def validate_size(self, value):
        if value <= 0:
            raise serializers.ValidationError("Backup size must be greater than zero.")
        return value


class MoveVirtualMachineSerializer(serializers.ModelSerializer):
    new_owner = serializers.CharField()

    class Meta:
        model = VirtualMachine
        fields = ['new_owner']

    def validate_new_owner(self, value):
        try:
            new_owner = CustomUser.objects.get(username=value)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("The specified user does not exist.")

        # Ensure that the new owner has the 'Standard User' role
        if new_owner.role.name != 'Standard User':
            raise serializers.ValidationError("The new owner must be a Standard User.")
        
        return new_owner


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['name', 'max_vms', 'max_backups', 'cost']

class BillingSerializer(serializers.ModelSerializer):
    subscription_plan = SubscriptionPlanSerializer()
    
    class Meta:
        model = Payment
        fields = ['amount', 'created_at', 'status', 'subscription_plan']  

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'cost', 'duration']


class UserSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscription
        fields = ['user', 'subscription_plan', 'started_at', 'expires_at']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['user', 'amount', 'status', 'transaction_id', 'created_at']


class BackupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Backup
        fields = '__all__'

class SnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Snapshot
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'

class UserSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscription
        fields = '__all__'

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'

