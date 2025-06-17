"""
Tests for Django Polls Application - Complete CRUD Validation

This module contains tests to validate the correct functioning of CRUD operations
for Questions and Choices, including the complex logic implemented in the serializer for:
- Creating questions with choices
- Updating existing questions
- Updating existing choices 
- Creating new choices
- Deleting choices not included in the update
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from polls.models import Question, Choice
import json


class QuestionModelTest(TestCase):
    """
    Tests to validate the Question model and its relationships with Choice
    """

    def setUp(self):
        """Initial setup for model tests"""
        self.question = Question.objects.create(
            question_text="What is your favorite framework?",
            pub_date=timezone.now()
        )

    def test_question_creation(self):
        """Test: Verify that a question can be created correctly"""
        self.assertEqual(self.question.question_text, "What is your favorite framework?")
        self.assertIsNotNone(self.question.pub_date)
        self.assertEqual(str(self.question), "What is your favorite framework?")

    def test_question_choice_relationship(self):
        """Test: Verify the relationship between Question and Choice with related_name='choices'"""
        choice1 = Choice.objects.create(
            question=self.question,
            choice_text="Django",
            votes=0
        )
        choice2 = Choice.objects.create(
            question=self.question,
            choice_text="FastAPI",
            votes=0
        )

        # Verify that the reverse relationship works correctly
        self.assertEqual(self.question.choices.count(), 2)
        self.assertIn(choice1, self.question.choices.all())
        self.assertIn(choice2, self.question.choices.all())

    def test_choice_deletion_on_question_delete(self):
        """Test: Verify that choices are deleted when question is deleted (CASCADE)"""
        Choice.objects.create(question=self.question, choice_text="Django")
        Choice.objects.create(question=self.question, choice_text="FastAPI")
        
        choice_count_before = Choice.objects.count()
        self.assertEqual(choice_count_before, 2)
        
        self.question.delete()
        
        choice_count_after = Choice.objects.count()
        self.assertEqual(choice_count_after, 0)


class QuestionAPICreateTest(TestCase):
    """
    Tests to validate Questions creation via API
    """

    def setUp(self):
        """Initial setup for creation tests"""
        self.client = APIClient()
        self.create_url = reverse('question-list')

    def test_create_question_with_choices(self):
        """Test: Create a question with choices using the API"""
        data = {
            "question": "What is your favorite programming language?",
            "choices": [
                {"choice_text": "Python"},
                {"choice_text": "JavaScript"},
                {"choice_text": "Java"}
            ]
        }

        response = self.client.post(self.create_url, data, format='json')
        
        # Verify successful response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify that the question was created correctly
        question = Question.objects.get(id=response.data['id'])
        self.assertEqual(question.question_text, "What is your favorite programming language?")
        self.assertIsNotNone(question.pub_date)
        
        # Verify that the choices were created correctly
        self.assertEqual(question.choices.count(), 3)
        choice_texts = [choice.choice_text for choice in question.choices.all()]
        self.assertIn("Python", choice_texts)
        self.assertIn("JavaScript", choice_texts)
        self.assertIn("Java", choice_texts)

    def test_create_question_without_choices(self):
        """Test: Create a question without choices"""
        data = {
            "question": "What do you think about Django?",
            "choices": []
        }

        response = self.client.post(self.create_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        question = Question.objects.get(id=response.data['id'])
        self.assertEqual(question.choices.count(), 0)

    def test_create_question_missing_required_fields(self):
        """Test: Try to create a question without required fields"""
        data = {"choices": []}  # Missing 'question' field

        response = self.client.post(self.create_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class QuestionAPIReadTest(TestCase):
    """
    Tests to validate Questions reading via API
    """

    def setUp(self):
        """Initial setup for read tests"""
        self.client = APIClient()
        
        # Create test data
        self.question1 = Question.objects.create(
            question_text="Question 1?",
            pub_date=timezone.now()
        )
        self.question2 = Question.objects.create(
            question_text="Question 2?",
            pub_date=timezone.now()
        )
        
        # Add choices to question1
        Choice.objects.create(question=self.question1, choice_text="Option 1", votes=0)
        Choice.objects.create(question=self.question1, choice_text="Option 2", votes=5)

    def test_list_questions(self):
        """Test: List all questions"""
        url = reverse('question-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_question_with_choices(self):
        """Test: Get a specific question with its choices"""
        url = reverse('question-detail', kwargs={'pk': self.question1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify response structure
        self.assertEqual(response.data['question'], "Question 1?")
        self.assertEqual(len(response.data['choices']), 2)
        
        # Verify that choices have the correct structure
        choice_texts = [choice['choice_text'] for choice in response.data['choices']]
        self.assertIn("Option 1", choice_texts)
        self.assertIn("Option 2", choice_texts)
        
        # Verify that each choice has an ID
        for choice in response.data['choices']:
            self.assertIn('id', choice)
            self.assertIn('choice_text', choice)

    def test_retrieve_nonexistent_question(self):
        """Test: Try to get a question that doesn't exist"""
        url = reverse('question-detail', kwargs={'pk': 9999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class QuestionAPIUpdateTest(TestCase):
    """
    Tests to validate Questions update via API
    Includes validation of complex serializer logic for choices
    """

    def setUp(self):
        """Initial setup for update tests"""
        self.client = APIClient()
        
        # Create question with initial choices
        self.question = Question.objects.create(
            question_text="Favorite web framework?",
            pub_date=timezone.now()
        )
        
        self.choice1 = Choice.objects.create(
            question=self.question,
            choice_text="Django",
            votes=0
        )
        self.choice2 = Choice.objects.create(
            question=self.question,
            choice_text="FastAPI",
            votes=0
        )
        self.choice3 = Choice.objects.create(
            question=self.question,
            choice_text="Flask",
            votes=0
        )
        
        self.update_url = reverse('question-detail', kwargs={'pk': self.question.pk})

    def test_update_question_text_only(self):
        """Test: Update only the question text while keeping existing choices"""
        data = {
            "question": "What is your preferred web framework?",
            "choices": [
                {"id": self.choice1.id, "choice_text": "Django"},
                {"id": self.choice2.id, "choice_text": "FastAPI"},
                {"id": self.choice3.id, "choice_text": "Flask"}
            ]
        }

        response = self.client.put(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify that the text was updated
        self.question.refresh_from_db()
        self.assertEqual(self.question.question_text, "What is your preferred web framework?")
        
        # Verify that choices were maintained
        self.assertEqual(self.question.choices.count(), 3)

    def test_update_existing_choices(self):
        """Test: Update existing choices"""
        data = {
            "question": "Favorite web framework?",
            "choices": [
                {"id": self.choice1.id, "choice_text": "Django Updated"},
                {"id": self.choice2.id, "choice_text": "FastAPI Updated"},
                {"id": self.choice3.id, "choice_text": "Flask Updated"}
            ]
        }

        response = self.client.put(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify that choices were updated
        self.choice1.refresh_from_db()
        self.choice2.refresh_from_db()
        self.choice3.refresh_from_db()
        
        self.assertEqual(self.choice1.choice_text, "Django Updated")
        self.assertEqual(self.choice2.choice_text, "FastAPI Updated")
        self.assertEqual(self.choice3.choice_text, "Flask Updated")

    def test_create_new_choices(self):
        """Test: Create new choices (without ID) along with existing choices"""
        data = {
            "question": "Favorite web framework?",
            "choices": [
                {"id": self.choice1.id, "choice_text": "Django"},
                {"choice_text": "Vue.js"},  # New choice without ID
                {"choice_text": "React"}    # New choice without ID
            ]
        }

        response = self.client.put(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify that new choices were created and non-included ones were deleted
        self.question.refresh_from_db()
        self.assertEqual(self.question.choices.count(), 3)
        
        choice_texts = [choice.choice_text for choice in self.question.choices.all()]
        self.assertIn("Django", choice_texts)
        self.assertIn("Vue.js", choice_texts)
        self.assertIn("React", choice_texts)
        
        # Verify that choice2 and choice3 were deleted
        self.assertNotIn("FastAPI", choice_texts)
        self.assertNotIn("Flask", choice_texts)

    def test_delete_choices_not_included(self):
        """Test: Delete choices not included in the update"""
        data = {
            "question": "Favorite web framework?",
            "choices": [
                {"id": self.choice1.id, "choice_text": "Django Only"}
            ]
        }

        response = self.client.put(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify that only one choice remains
        self.question.refresh_from_db()
        self.assertEqual(self.question.choices.count(), 1)
        self.assertEqual(self.question.choices.first().choice_text, "Django Only")

    def test_mixed_update_operations(self):
        """Test: Mix of operations - update, create and delete choices"""
        data = {
            "question": "Updated favorite web framework?",
            "choices": [
                {"id": self.choice1.id, "choice_text": "Django Modified"},  # Update
                {"choice_text": "Svelte"},  # Create new
                {"choice_text": "Angular"}  # Create new
                # choice2 and choice3 will be deleted because they're not included
            ]
        }

        response = self.client.put(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify all changes
        self.question.refresh_from_db()
        self.assertEqual(self.question.question_text, "Updated favorite web framework?")
        self.assertEqual(self.question.choices.count(), 3)
        
        choice_texts = [choice.choice_text for choice in self.question.choices.all()]
        self.assertIn("Django Modified", choice_texts)
        self.assertIn("Svelte", choice_texts)
        self.assertIn("Angular", choice_texts)
        
        # Verify that original choices were deleted
        self.assertNotIn("FastAPI", choice_texts)
        self.assertNotIn("Flask", choice_texts)

    def test_update_with_empty_choices(self):
        """Test: Update question by deleting all choices"""
        data = {
            "question": "Question without options?",
            "choices": []
        }

        response = self.client.put(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify that all choices were deleted
        self.question.refresh_from_db()
        self.assertEqual(self.question.choices.count(), 0)

    def test_update_nonexistent_question(self):
        """Test: Try to update a question that doesn't exist"""
        url = reverse('question-detail', kwargs={'pk': 9999})
        data = {"question": "Test", "choices": []}

        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class QuestionAPIDeleteTest(TestCase):
    """
    Tests to validate Questions deletion via API
    """

    def setUp(self):
        """Initial setup for deletion tests"""
        self.client = APIClient()
        
        self.question = Question.objects.create(
            question_text="Question to delete?",
            pub_date=timezone.now()
        )
        
        # Add choices to verify they are also deleted
        Choice.objects.create(question=self.question, choice_text="Option 1")
        Choice.objects.create(question=self.question, choice_text="Option 2")
        
        self.delete_url = reverse('question-detail', kwargs={'pk': self.question.pk})

    def test_delete_question(self):
        """Test: Delete a question and verify that choices are also deleted"""
        # Verify initial state
        self.assertEqual(Question.objects.count(), 1)
        self.assertEqual(Choice.objects.count(), 2)

        response = self.client.delete(self.delete_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify that question and its choices were deleted
        self.assertEqual(Question.objects.count(), 0)
        self.assertEqual(Choice.objects.count(), 0)

    def test_delete_nonexistent_question(self):
        """Test: Try to delete a question that doesn't exist"""
        url = reverse('question-detail', kwargs={'pk': 9999})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class QuestionAPIDeleteExtendedTest(TestCase):
    """
    Extended tests to validate complete Questions deletion via API
    Includes different scenarios and edge cases for DELETE operation
    """

    def setUp(self):
        """Initial setup for extended deletion tests"""
        self.client = APIClient()

    def test_delete_question_with_many_choices(self):
        """Test: Delete question with many choices and verify complete CASCADE"""
        question = Question.objects.create(
            question_text="Question with many choices?",
            pub_date=timezone.now()
        )
        
        # Create multiple choices with different vote values
        choices_data = [
            {"choice_text": f"Option {i}", "votes": i * 10}
            for i in range(1, 11)  # 10 choices
        ]
        
        for choice_data in choices_data:
            Choice.objects.create(question=question, **choice_data)
        
        # Verify initial state
        self.assertEqual(Question.objects.count(), 1)
        self.assertEqual(Choice.objects.count(), 10)
        self.assertEqual(question.choices.count(), 10)
        
        # Delete question
        url = reverse('question-detail', kwargs={'pk': question.pk})
        response = self.client.delete(url)
        
        # Verify successful deletion
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Question.objects.count(), 0)
        self.assertEqual(Choice.objects.count(), 0)

    def test_delete_question_without_choices(self):
        """Test: Delete question that has no choices"""
        question = Question.objects.create(
            question_text="Question without choices?",
            pub_date=timezone.now()
        )
        
        # Verify it has no choices
        self.assertEqual(question.choices.count(), 0)
        self.assertEqual(Question.objects.count(), 1)
        
        # Delete question
        url = reverse('question-detail', kwargs={'pk': question.pk})
        response = self.client.delete(url)
        
        # Verify successful deletion
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Question.objects.count(), 0)

    def test_delete_multiple_questions_sequentially(self):
        """Test: Delete multiple questions sequentially"""
        # Create multiple questions with choices
        questions = []
        for i in range(1, 4):
            question = Question.objects.create(
                question_text=f"Question {i}?",
                pub_date=timezone.now()
            )
            
            # Add choices to each question
            Choice.objects.create(question=question, choice_text=f"Choice 1 of Q{i}")
            Choice.objects.create(question=question, choice_text=f"Choice 2 of Q{i}")
            questions.append(question)
        
        # Verify initial state
        self.assertEqual(Question.objects.count(), 3)
        self.assertEqual(Choice.objects.count(), 6)
        
        # Delete questions one by one
        for i, question in enumerate(questions):
            url = reverse('question-detail', kwargs={'pk': question.pk})
            response = self.client.delete(url)
            
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            
            # Verify counts after each deletion
            remaining_questions = 3 - (i + 1)
            remaining_choices = remaining_questions * 2
            
            self.assertEqual(Question.objects.count(), remaining_questions)
            self.assertEqual(Choice.objects.count(), remaining_choices)
        
        # Verify final state
        self.assertEqual(Question.objects.count(), 0)
        self.assertEqual(Choice.objects.count(), 0)

    def test_delete_question_with_specific_choice_ids(self):
        """Test: Verify that specific choice IDs are freed correctly"""
        question = Question.objects.create(
            question_text="Test IDs?",
            pub_date=timezone.now()
        )
        
        choice1 = Choice.objects.create(question=question, choice_text="Choice 1")
        choice2 = Choice.objects.create(question=question, choice_text="Choice 2")
        choice3 = Choice.objects.create(question=question, choice_text="Choice 3")
        
        # Save IDs before deletion
        choice_ids = [choice1.id, choice2.id, choice3.id]
        question_id = question.id
        
        # Delete question
        url = reverse('question-detail', kwargs={'pk': question.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify that no objects with those IDs exist
        self.assertFalse(Question.objects.filter(id=question_id).exists())
        for choice_id in choice_ids:
            self.assertFalse(Choice.objects.filter(id=choice_id).exists())

    def test_delete_question_after_getting_detail(self):
        """Test: Delete question after getting its detail (common user flow)"""
        question = Question.objects.create(
            question_text="Question for GET->DELETE flow?",
            pub_date=timezone.now()
        )
        
        Choice.objects.create(question=question, choice_text="Option A", votes=5)
        Choice.objects.create(question=question, choice_text="Option B", votes=3)
        
        url = reverse('question-detail', kwargs={'pk': question.pk})
        
        # Step 1: Get question detail
        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data['question'], "Question for GET->DELETE flow?")
        self.assertEqual(len(get_response.data['choices']), 2)
        
        # Step 2: Delete the question
        delete_response = self.client.delete(url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Step 3: Verify it can no longer be retrieved
        final_get_response = self.client.get(url)
        self.assertEqual(final_get_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_question_idempotency(self):
        """Test: Verify DELETE idempotency (try to delete twice)"""
        question = Question.objects.create(
            question_text="Test idempotency?",
            pub_date=timezone.now()
        )
        
        Choice.objects.create(question=question, choice_text="Choice for test")
        
        url = reverse('question-detail', kwargs={'pk': question.pk})
        
        # First deletion
        first_response = self.client.delete(url)
        self.assertEqual(first_response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Second deletion (should return 404)
        second_response = self.client.delete(url)
        self.assertEqual(second_response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify no objects in DB
        self.assertEqual(Question.objects.count(), 0)
        self.assertEqual(Choice.objects.count(), 0)

    def test_delete_question_with_mixed_operations_before(self):
        """Test: Delete question after performing previous CRUD operations"""
        # Create initial question
        create_data = {
            "question": "Test mixed operations?",
            "choices": [
                {"choice_text": "Initial 1"},
                {"choice_text": "Initial 2"}
            ]
        }
        
        create_response = self.client.post(reverse('question-list'), create_data, format='json')
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        question_id = create_response.data['id']
        
        # Read question
        detail_url = reverse('question-detail', kwargs={'pk': question_id})
        read_response = self.client.get(detail_url)
        self.assertEqual(read_response.status_code, status.HTTP_200_OK)
        
        # Update question
        choice_id = read_response.data['choices'][0]['id']
        update_data = {
            "question": "Test mixed operations updated?",
            "choices": [
                {"id": choice_id, "choice_text": "Updated"},
                {"choice_text": "New choice"}
            ]
        }
        
        update_response = self.client.put(detail_url, update_data, format='json')
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        
        # Verify state before deletion
        verify_response = self.client.get(detail_url)
        self.assertEqual(len(verify_response.data['choices']), 2)
        
        # Finally, delete question
        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify complete deletion
        self.assertEqual(Question.objects.count(), 0)
        self.assertEqual(Choice.objects.count(), 0)

    def test_delete_question_with_invalid_id_formats(self):
        """Test: Try to delete with invalid ID formats"""
        invalid_ids = ['abc', '0', '-1', '99999999999999999999', 'null', '']
        
        for invalid_id in invalid_ids:
            if invalid_id:  # Avoid empty URL
                url = f"/polls/api/questions/{invalid_id}/"
                response = self.client.delete(url)
                
                # Should return 404 or 400 depending on format
                self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST])

    def test_delete_question_response_content(self):
        """Test: Verify that DELETE response contains no content"""
        question = Question.objects.create(
            question_text="Test DELETE response?",
            pub_date=timezone.now()
        )
        
        url = reverse('question-detail', kwargs={'pk': question.pk})
        response = self.client.delete(url)
        
        # Verify status code and empty content
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.content), 0)
        
        # Verify that Content-Length is 0 (standard for 204 responses)
        self.assertEqual(response.headers.get('Content-Length'), '0')
        
        # Verify other standard headers are present
        self.assertIn('X-Frame-Options', response.headers)
        self.assertIn('X-Content-Type-Options', response.headers)


class QuestionSerializerEdgeCasesTest(TestCase):
    """
    Tests for serializer edge cases and special validations
    """

    def setUp(self):
        """Initial setup for edge case tests"""
        self.client = APIClient()

    def test_create_question_with_duplicate_choice_texts(self):
        """Test: Create question with choices that have the same text"""
        data = {
            "question": "Test duplicates?",
            "choices": [
                {"choice_text": "Duplicate Option"},
                {"choice_text": "Duplicate Option"},
                {"choice_text": "Unique Option"}
            ]
        }

        response = self.client.post(reverse('question-list'), data, format='json')
        
        # Should allow duplicate choices (no validation prevents it)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        question = Question.objects.get(id=response.data['id'])
        self.assertEqual(question.choices.count(), 3)

    def test_update_with_invalid_choice_id(self):
        """Test: Update with choice ID that doesn't exist"""
        question = Question.objects.create(
            question_text="Test question?",
            pub_date=timezone.now()
        )
        
        data = {
            "question": "Test question?",
            "choices": [
                {"id": 9999, "choice_text": "Choice with non-existent ID"}
            ]
        }

        url = reverse('question-detail', kwargs={'pk': question.pk})
        response = self.client.put(url, data, format='json')
        
        # Should create a new choice since ID doesn't exist
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        question.refresh_from_db()
        self.assertEqual(question.choices.count(), 1)

    def test_partial_update_patch(self):
        """Test: Partial update using PATCH"""
        question = Question.objects.create(
            question_text="Original question?",
            pub_date=timezone.now()
        )
        
        data = {"question": "Updated question?"}

        url = reverse('question-detail', kwargs={'pk': question.pk})
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        question.refresh_from_db()
        self.assertEqual(question.question_text, "Updated question?")


class QuestionAPIIntegrationTest(TestCase):
    """
    Integration tests that validate complete application workflows
    """

    def setUp(self):
        """Setup for integration tests"""
        self.client = APIClient()

    def test_complete_crud_workflow(self):
        """Test: Complete CRUD workflow - Create, Read, Update, Delete"""
        
        # 1. CREATE - Create question with choices
        create_data = {
            "question": "Best database?",
            "choices": [
                {"choice_text": "PostgreSQL"},
                {"choice_text": "MySQL"},
                {"choice_text": "MongoDB"}
            ]
        }
        
        create_response = self.client.post(reverse('question-list'), create_data, format='json')
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        question_id = create_response.data['id']
        
        # 2. READ - Read the created question
        detail_url = reverse('question-detail', kwargs={'pk': question_id})
        read_response = self.client.get(detail_url)
        self.assertEqual(read_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(read_response.data['choices']), 3)
        
        # 3. UPDATE - Update question and choices
        choice_id = read_response.data['choices'][0]['id']
        update_data = {
            "question": "Best database system?",
            "choices": [
                {"id": choice_id, "choice_text": "PostgreSQL Updated"},
                {"choice_text": "SQLite"}  # New choice
                # Other choices will be deleted
            ]
        }
        
        update_response = self.client.put(detail_url, update_data, format='json')
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        
        # Verify update
        verify_response = self.client.get(detail_url)
        self.assertEqual(len(verify_response.data['choices']), 2)
        
        # 4. DELETE - Delete question
        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify deletion
        final_response = self.client.get(detail_url)
        self.assertEqual(final_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_concurrent_updates_simulation(self):
        """Test: Simulate concurrent updates to verify consistency"""
        
        # Create initial question
        question = Question.objects.create(
            question_text="Test concurrency?",
            pub_date=timezone.now()
        )
        choice = Choice.objects.create(question=question, choice_text="Original")
        
        url = reverse('question-detail', kwargs={'pk': question.pk})
        
        # Simulate two "concurrent" updates
        update1_data = {
            "question": "Test concurrency updated 1?",
            "choices": [{"id": choice.id, "choice_text": "Updated 1"}]
        }
        
        update2_data = {
            "question": "Test concurrency updated 2?", 
            "choices": [{"id": choice.id, "choice_text": "Updated 2"}]
        }
        
        # Execute updates
        response1 = self.client.put(url, update1_data, format='json')
        response2 = self.client.put(url, update2_data, format='json')
        
        # Both should be successful
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Verify final state (last update should prevail)
        final_response = self.client.get(url)
        self.assertEqual(final_response.data['question'], "Test concurrency updated 2?")

    def test_complete_crud_workflow_with_extended_delete(self):
        """Test: Complete CRUD workflow with extended DELETE validation"""
        
        # Create multiple questions to test selective deletion
        questions_data = [
            {"question": "Question 1?", "choices": [{"choice_text": "A1"}, {"choice_text": "B1"}]},
            {"question": "Question 2?", "choices": [{"choice_text": "A2"}, {"choice_text": "B2"}]},
            {"question": "Question 3?", "choices": [{"choice_text": "A3"}, {"choice_text": "B3"}]}
        ]
        
        created_questions = []
        for data in questions_data:
            response = self.client.post(reverse('question-list'), data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            created_questions.append(response.data['id'])
        
        # Verify all were created
        self.assertEqual(Question.objects.count(), 3)
        self.assertEqual(Choice.objects.count(), 6)
        
        # Delete the middle question
        middle_question_id = created_questions[1]
        middle_url = reverse('question-detail', kwargs={'pk': middle_question_id})
        delete_response = self.client.delete(middle_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify selective deletion
        self.assertEqual(Question.objects.count(), 2)
        self.assertEqual(Choice.objects.count(), 4)
        
        # Verify other questions still work
        for question_id in [created_questions[0], created_questions[2]]:
            url = reverse('question-detail', kwargs={'pk': question_id})
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['choices']), 2)
        
        # Verify deleted question doesn't exist
        deleted_response = self.client.get(middle_url)
        self.assertEqual(deleted_response.status_code, status.HTTP_404_NOT_FOUND)
