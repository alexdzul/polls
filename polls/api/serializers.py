from rest_framework import serializers
from ..models import Question, Choice
from django.utils import timezone

class ChoiceSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    
    class Meta:
        model = Choice
        fields = ['id', 'choice_text']

class QuestionSerializer(serializers.ModelSerializer):
    question = serializers.CharField(source='question_text')
    choices = ChoiceSerializer(many=True)

    class Meta:
        model = Question
        fields = ['id', 'question', 'choices']

    def create(self, validated_data):
        """
        Create a new question with choices.
        """
        choices_data = validated_data.pop('choices', [])
        validated_data['pub_date'] = timezone.now()
        question = Question.objects.create(**validated_data)
        for choice_data in choices_data:
            Choice.objects.create(question=question, **choice_data)
        return question
    
    def update(self, instance, validated_data):
        """
        Update a question and its choices.
        """
        choices_data = validated_data.pop('choices', [])
        
        # Step 1: Update question fields
        instance.question_text = validated_data.get('question_text', instance.question_text)
        instance.save()
        
        # Step 2: Handle choices update
        # Get existing choices first (always, regardless of choices_data)
        existing_choices = {choice.id: choice for choice in instance.choices.all()}
        
        if choices_data:
            updated_choice_ids = set()
            
            for choice_data in choices_data:
                choice_id = choice_data.get('id')
                choice_text = choice_data.get('choice_text')
                
                if choice_id and choice_id in existing_choices:
                    # Step 2.1: Update existing choice
                    choice = existing_choices[choice_id]
                    choice.choice_text = choice_data.get('choice_text', choice.choice_text)
                    choice.save()
                    updated_choice_ids.add(choice_id)
                else:
                    # Step 2.2: Create new choice (either no ID provided or ID doesn't exist)
                    new_choice = Choice.objects.create(question=instance, choice_text=choice_text)
                    updated_choice_ids.add(new_choice.id)
            
            # Step 3: Delete choices that weren't included in the update
            for choice_id, choice in existing_choices.items():
                if choice_id not in updated_choice_ids:
                    choice.delete()
        else:
            # If choices_data is empty, delete all existing choices
            for choice in existing_choices.values():
                choice.delete()
        
        return instance