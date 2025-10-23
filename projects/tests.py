from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Project, ProjectTeamMember, ProjectVendor

User = get_user_model()

class DeletePermissionsTests(TestCase):
    def setUp(self):
        # create users
        self.admin = User.objects.create_user(username='admin', password='pass')
        self.admin.level = 'Admin'
        self.admin.save()

        self.owner = User.objects.create_user(username='owner', password='pass')
        self.creator = User.objects.create_user(username='creator', password='pass')
        self.approver = User.objects.create_user(username='approver', password='pass')
        self.other = User.objects.create_user(username='other', password='pass')

        # create project owned by owner
        self.project = Project.objects.create(name='TestProj', project_number='TP1', owner=self.owner)

        # add team member and vendor
        self.team_member = ProjectTeamMember.objects.create(project=self.project, user=self.creator)
        self.vendor = ProjectVendor.objects.create(project=self.project, user=self.creator)

    def post_delete(self, user, url_name, kwargs):
        self.client.force_login(user)
        return self.client.post(reverse(url_name, kwargs=kwargs))

    def test_admin_can_delete_member(self):
        resp = self.post_delete(self.admin, 'team_member_delete', {'project_pk': self.project.pk, 'member_pk': self.team_member.pk})
        self.assertRedirects(resp, reverse('project_detail', kwargs={'pk': self.project.pk}))
        self.assertFalse(ProjectTeamMember.objects.filter(pk=self.team_member.pk).exists())

    def test_owner_can_delete_member(self):
        resp = self.post_delete(self.owner, 'team_member_delete', {'project_pk': self.project.pk, 'member_pk': self.team_member.pk})
        self.assertRedirects(resp, reverse('project_detail', kwargs={'pk': self.project.pk}))
        self.assertFalse(ProjectTeamMember.objects.filter(pk=self.team_member.pk).exists())

    def test_member_can_remove_self(self):
        # creator removes their own association
        resp = self.post_delete(self.creator, 'team_member_delete', {'project_pk': self.project.pk, 'member_pk': self.team_member.pk})
        self.assertRedirects(resp, reverse('project_detail', kwargs={'pk': self.project.pk}))
        self.assertFalse(ProjectTeamMember.objects.filter(pk=self.team_member.pk).exists())

    def test_other_cannot_delete_member(self):
        # other user should get 403
        self.client.force_login(self.other)
        resp = self.client.post(reverse('team_member_delete', kwargs={'project_pk': self.project.pk, 'member_pk': self.team_member.pk}))
        self.assertEqual(resp.status_code, 403)

    def test_admin_can_delete_vendor(self):
        resp = self.post_delete(self.admin, 'vendor_delete', {'project_pk': self.project.pk, 'vendor_pk': self.vendor.pk})
        self.assertRedirects(resp, reverse('project_detail', kwargs={'pk': self.project.pk}))
        self.assertFalse(ProjectVendor.objects.filter(pk=self.vendor.pk).exists())

    def test_owner_can_delete_vendor(self):
        resp = self.post_delete(self.owner, 'vendor_delete', {'project_pk': self.project.pk, 'vendor_pk': self.vendor.pk})
        self.assertRedirects(resp, reverse('project_detail', kwargs={'pk': self.project.pk}))
        self.assertFalse(ProjectVendor.objects.filter(pk=self.vendor.pk).exists())

    def test_vendor_can_remove_self(self):
        resp = self.post_delete(self.creator, 'vendor_delete', {'project_pk': self.project.pk, 'vendor_pk': self.vendor.pk})
        self.assertRedirects(resp, reverse('project_detail', kwargs={'pk': self.project.pk}))
        self.assertFalse(ProjectVendor.objects.filter(pk=self.vendor.pk).exists())

    def test_other_cannot_delete_vendor(self):
        self.client.force_login(self.other)
        resp = self.client.post(reverse('vendor_delete', kwargs={'project_pk': self.project.pk, 'vendor_pk': self.vendor.pk}))
        self.assertEqual(resp.status_code, 403)
