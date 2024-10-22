#!/bin/sh
echo ' 118.214 Info ServerSynchronizer.cpp:604: nextHeartbeatSequenceNumber(64747) adding peer(2)'
sleep 1
echo ' 118.214 Info ServerMultiplayerManager.cpp:795: updateTick(176585302) changing state from(InGame) to(InGameSavingMap)'
sleep 1
echo ' 118.214 Info ServerMultiplayerManager.cpp:944: updateTick(176585302) received stateChanged peerID(2) oldState(Ready) newState(ConnectedWaitingForMap)'
sleep 1
echo ' 121.214 Info ServerMultiplayerManager.cpp:1005: UpdateTick(176585302) Serving map(/factorio/temp/mp-save-1.zip) for peer(2) size(169444468) auxiliary(317) crc(3774189260)'
sleep 1
echo ' 121.214 Info ServerMultiplayerManager.cpp:795: updateTick(176585302) changing state from(InGameSavingMap) to(InGame)'
sleep 1
echo ' 121.284 Info ServerMultiplayerManager.cpp:944: updateTick(176585308) received stateChanged peerID(2) oldState(ConnectedWaitingForMap) newState(ConnectedDownloadingMap)'
sleep 1
echo ' 133.509 Info ServerMultiplayerManager.cpp:944: updateTick(176585556) received stateChanged peerID(2) oldState(ConnectedDownloadingMap) newState(ConnectedLoadingMap)'
sleep 1
echo ' 140.643 Info ServerMultiplayerManager.cpp:944: updateTick(176585556) received stateChanged peerID(2) oldState(ConnectedLoadingMap) newState(TryingToCatchUp)'
sleep 1
echo ' 142.476 Info ServerMultiplayerManager.cpp:944: updateTick(176585556) received stateChanged peerID(2) oldState(TryingToCatchUp) newState(WaitingForCommandToStartSendingTickClosures)'
sleep 1
echo ' 142.526 Info ServerMultiplayerManager.cpp:944: updateTick(176585556) received stateChanged peerID(2) oldState(WaitingForCommandToStartSendingTickClosures) newState(InGame)'
sleep 1
echo ' 1116.526 Info ServerSynchronizer.cpp:623: nextHeartbeatSequenceNumber(66276) removing peer(2).'
sleep 1
