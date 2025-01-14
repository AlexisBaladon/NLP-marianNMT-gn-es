import os

from ..utils import process_manager
from ..utils import parsing
from ..utils import file_manager
from src.domain.evaluation import metrics
from ..config import command_config

# Renames the checkpoint with the format model-<after_epochs>.<extension>
def rename_checkpoint(model_dir, added_str):
    # type: (str, str) -> str
    model_dir = model_dir.split('.')
    model_checkpoint_path = model_dir[:-1]
    model_checkpoint_path = '.'.join(model_checkpoint_path)
    model_checkpoint_path += '-{}'.format(added_str)
    model_checkpoint_path += '.' + model_dir[-1]
    return model_checkpoint_path

def validate(flags,
             base_dir_evaluation,
             model_dir, 
             command_name,
             validation_metrics=None, 
             batch_size=None,
             after_epochs=None,
             validation_log=None,
             valid_tgt=None,
             validation_translation_output=None,):
    # type: (dict[str, list[str]], str, str, list[str], str, str, str, str, str, str) -> list
    evaluation_file = os.path.join(base_dir_evaluation, command_name)
    validation_translation_output_path = None
    if validation_translation_output is not None:
        validation_translation_output_path = \
            parsing.parse_output_filename(validation_translation_output, 
                                          epoch=after_epochs,
                                          batch=batch_size)
    results = metrics.save_results(file_name=evaluation_file,
                                   model_dir=model_dir,
                                   parameters=flags,
                                   metrics=validation_metrics,
                                   validation_log=validation_log,
                                   translation_output=validation_translation_output_path,
                                   reference=valid_tgt)
    return results

def validation_enabled(validation_metrics, 
                       artificial_epoch_training, 
                       validation_log, model_metrics, 
                       validation_translation_output):
    # type: (list[str], bool, str, list[str], str) -> bool    
    if artificial_epoch_training and \
       'translation' in model_metrics and \
       validation_metrics is not None and \
       len(validation_metrics) > 0 and \
       validation_translation_output is not None and \
       True:
        return True
    
    if not artificial_epoch_training and validation_log is not None:
        return True
    
    return False

def handle_non_first_config(marian_config, 
                            to_delete_flags=['no-restore-corpus']):
    # type: (command_config.CommandConfig, list[str]) -> command_config.CommandConfig
    for to_delete_flag in to_delete_flags:
        if to_delete_flag in marian_config.flags:
            del marian_config.flags[to_delete_flag]
        return marian_config

def simple_training(marian_config, 
                    is_validation_enabled, 
                    flags, 
                    base_dir_evaluation, 
                    model_dir, 
                    command_name, 
                    validation_log):
    # type: (command_config.CommandConfig, bool, dict[str, list[str]], str, str, str, str) -> None
    command = parsing.create_command(marian_config)
    process_manager.run_command(command)

    if is_validation_enabled:
        validate(flags=flags,
                 base_dir_evaluation=base_dir_evaluation,
                 model_dir=model_dir, 
                 command_name=command_name,
                 validation_log=validation_log)

def training_with_artificial_epochs(marian_config,
                                    is_validation_enabled,
                                    flags,
                                    base_dir_evaluation,
                                    validation_translation_output,
                                    train_from_epoch,
                                    after_epochs,
                                    batch_size,
                                    valid_tgt,
                                    model_dir,
                                    validation_metrics,
                                    command_name,
                                    save_checkpoints,
                                    validate_each_epochs,
                                    early_stopping):
    # type: (command_config.CommandConfig, bool, dict[str, list[str]], str, str, int, str, str, str, str, list[str], str, bool, int, int) -> None
    train_from_epoch, after_epochs, validate_each_epochs = \
        map(int, (train_from_epoch, after_epochs, validate_each_epochs))
    artificial_epochs = after_epochs//validate_each_epochs
    first_epoch_idx = train_from_epoch//validate_each_epochs

    # Model should not receive early-stopping, but validation logs should
    logged_flags = flags

    if early_stopping is not None:
        early_stopping = int(early_stopping)
        marian_config = marian_config.copy(deep=True)
        marian_config.flags['early-stopping'] = ['10000'] # The default Marian early-stopping is 10. after_epochs is high enough to avoid it.
        early_stopping_metric_criteria = validation_metrics[0] \
            if validation_metrics is not None else None # Take first metric as early-stopping criteria
        most_importance_scores = {early_stopping_metric_criteria: []}
    
    for i in range(first_epoch_idx, artificial_epochs):
        current_after_epochs = validate_each_epochs * (i+1)

        if i > first_epoch_idx:
            marian_config = handle_non_first_config(marian_config)

        marian_config.flags['after-epochs'] = [str(current_after_epochs)]
        logged_flags['after-epochs'] = [str(current_after_epochs)]

        command = parsing.create_command(marian_config)
        process_manager.run_command(command)

        if save_checkpoints:
            checkpoint_path = rename_checkpoint(model_dir, current_after_epochs)
            file_manager.save_copy(model_dir, checkpoint_path)

        if is_validation_enabled:
            current_scores = validate(flags=logged_flags,
                                      base_dir_evaluation=base_dir_evaluation,
                                      validation_translation_output=validation_translation_output,
                                      after_epochs=current_after_epochs,
                                      batch_size=batch_size,
                                      valid_tgt=valid_tgt,
                                      model_dir=model_dir, 
                                      validation_metrics=validation_metrics, 
                                      command_name=command_name)

            if early_stopping is not None:
                current_most_important_scores = current_scores[early_stopping_metric_criteria]
                most_importance_scores[early_stopping_metric_criteria].extend(current_most_important_scores)

        
        if early_stopping is not None and early_stopping_metric_criteria is not None:
            current_most_important_scores = most_importance_scores[early_stopping_metric_criteria]

            if len(current_most_important_scores) < 2:
                continue

            if current_most_important_scores[-2] == current_most_important_scores[-1]:
                print('Constant metric evaluations detected ({} -> {}). \
                      Stopping after {} epochs'.format(
                            current_most_important_scores[-2], 
                            current_most_important_scores[-1], 
                            current_after_epochs))
                return
            
            if len(current_most_important_scores) <= early_stopping:
                continue

            max_score = max(current_most_important_scores)
            last_n_scores = current_most_important_scores[-early_stopping:]
            if all([score < max_score for score in last_n_scores]):
                print('Early stopping after {} epochs'.format(current_after_epochs))
                return
            

def train(command_config):
    # type: (command_config.CommandConfig) -> None
    marian_config = command_config.copy(deep=True)
    flags = marian_config.flags
    model_metrics = flags.get('valid-metrics', [])
    validation_translation_output = flags.get('valid-translation-output', 
                                              [None])[0]
    _, valid_tgt = flags.get('valid-sets', [None, None])
    validation_log = flags.get('valid-log', [None])[0]
    early_stopping = flags.get('early-stopping', [None])[0]
    model_dir = flags.get('model', [None])[0]
    after_epochs = flags.get('after-epochs', [None])[0]
    batch_size = flags.get('after-batches', [None])[0]
    train_from_epoch = marian_config.train_from_epoch
    validate_each_epochs = marian_config.validate_each_epochs
    validation_metrics = marian_config.validation_metrics
    base_dir_evaluation = marian_config.base_dir_evaluation
    save_checkpoints = marian_config.save_checkpoints
    command_name = marian_config.command_name
    not_delete_model_after = marian_config.not_delete_model_after
    artificial_epoch_training = validate_each_epochs is not None
    model_base_dir = os.path.dirname(model_dir)
    is_validation_enabled = validation_enabled(validation_metrics, 
                                                artificial_epoch_training, 
                                                validation_log, 
                                                model_metrics, 
                                                validation_translation_output)

    if not artificial_epoch_training:
        simple_training(marian_config=marian_config,
                        is_validation_enabled=is_validation_enabled,
                        flags=flags,
                        base_dir_evaluation=base_dir_evaluation,
                        model_dir=model_dir,
                        command_name=command_name,
                        validation_log=validation_log)
    else:
        training_with_artificial_epochs(marian_config=marian_config,
                                        is_validation_enabled=is_validation_enabled,
                                        flags=flags,
                                        base_dir_evaluation=base_dir_evaluation,
                                        validation_translation_output=validation_translation_output,
                                        train_from_epoch=train_from_epoch,
                                        after_epochs=after_epochs,
                                        batch_size=batch_size,
                                        valid_tgt=valid_tgt,
                                        model_dir=model_dir,
                                        validation_metrics=validation_metrics,
                                        command_name=command_name,
                                        save_checkpoints=save_checkpoints,
                                        validate_each_epochs=validate_each_epochs,
                                        early_stopping=early_stopping)

    if not not_delete_model_after:
        file_manager.delete_files(model_base_dir)