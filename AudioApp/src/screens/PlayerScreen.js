import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  StatusBar,
  Alert,
} from 'react-native';
import { Audio } from 'expo-av';
import { Ionicons } from '@expo/vector-icons';

export default function PlayerScreen({ route, navigation }) {
  const { lesson } = route.params;

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentSentenceIndex, setCurrentSentenceIndex] = useState(0);
  const [showTranslation, setShowTranslation] = useState(true);
  const [loopSentence, setLoopSentence] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);
  const [playCount, setPlayCount] = useState(0);
  const [sentencePlayCounts, setSentencePlayCounts] = useState({});

  const soundRef = useRef(null);

  useEffect(() => {
    navigation.setOptions({
      title: lesson.title,
      headerStyle: {
        backgroundColor: '#2196F3',
      },
      headerTintColor: '#fff',
      headerTitleStyle: {
        fontWeight: 'bold',
      },
    });

    return () => {
      if (soundRef.current) {
        soundRef.current.unloadAsync();
      }
    };
  }, []);

  // 播放当前句子
  const playCurrentSentence = async () => {
    try {
      // 注意：这里需要实际的音频文件
      // const sentence = lesson.sentences[currentSentenceIndex];
      // if (!sentence.audio) {
      //   Alert.alert('提示', '该句子暂无音频');
      //   return;
      // }

      // 模拟播放
      setIsPlaying(true);
      setPlayCount(prev => prev + 1);
      setSentencePlayCounts(prev => ({
        ...prev,
        [currentSentenceIndex]: (prev[currentSentenceIndex] || 0) + 1,
      }));

      // 模拟播放2秒
      setTimeout(() => {
        setIsPlaying(false);
        if (!loopSentence) {
          nextSentence();
        } else {
          // 循环播放当前句子
          setTimeout(() => {
            playCurrentSentence();
          }, 500);
        }
      }, 2000);

      // 实际使用时的代码：
      /*
      if (soundRef.current) {
        await soundRef.current.unloadAsync();
      }

      const { sound } = await Audio.Sound.createAsync(
        { uri: sentence.audio },
        { shouldPlay: true, rate: playbackSpeed }
      );
      soundRef.current = sound;

      sound.setOnPlaybackStatusUpdate((status) => {
        if (status.didJustFinish) {
          setIsPlaying(false);
          if (!loopSentence) {
            nextSentence();
          } else {
            setTimeout(() => {
              playCurrentSentence();
            }, 500);
          }
        }
      });
      */
    } catch (error) {
      console.error('播放错误:', error);
      Alert.alert('错误', '播放失败');
    }
  };

  const stopPlaying = () => {
    setIsPlaying(false);
    if (soundRef.current) {
      soundRef.current.stopAsync();
    }
  };

  const nextSentence = () => {
    if (currentSentenceIndex < lesson.sentences.length - 1) {
      setCurrentSentenceIndex(prev => prev + 1);
    }
  };

  const previousSentence = () => {
    if (currentSentenceIndex > 0) {
      setCurrentSentenceIndex(prev => prev - 1);
    }
  };

  const togglePlayPause = () => {
    if (isPlaying) {
      stopPlaying();
    } else {
      playCurrentSentence();
    }
  };

  const changeSpeed = () => {
    const speeds = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0];
    const currentIndex = speeds.indexOf(playbackSpeed);
    const nextIndex = (currentIndex + 1) % speeds.length;
    setPlaybackSpeed(speeds[nextIndex]);
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#2196F3" />

      {/* 课文信息 */}
      <View style={styles.header}>
        <Text style={styles.lessonTitle}>{lesson.title}</Text>
        <Text style={styles.lessonTitleCn}>{lesson.titleCn}</Text>
        <Text style={styles.playCountText}>总播放次数: {playCount}</Text>
      </View>

      {/* 句子显示区域 */}
      <ScrollView style={styles.contentArea}>
        {lesson.sentences.map((sentence, index) => (
          <TouchableOpacity
            key={index}
            style={[
              styles.sentenceCard,
              currentSentenceIndex === index && styles.sentenceCardActive,
            ]}
            onPress={() => setCurrentSentenceIndex(index)}
          >
            <View style={styles.sentenceHeader}>
              <Text style={styles.sentenceNumber}>句子 {index + 1}</Text>
              {sentencePlayCounts[index] > 0 && (
                <Text style={styles.sentencePlayCount}>
                  播放 {sentencePlayCounts[index]} 次
                </Text>
              )}
            </View>
            <Text style={styles.sentenceEn}>{sentence.en}</Text>
            {showTranslation && (
              <Text style={styles.sentenceCn}>{sentence.cn}</Text>
            )}
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* 控制面板 */}
      <View style={styles.controlPanel}>
        {/* 功能按钮 */}
        <View style={styles.optionsRow}>
          <TouchableOpacity
            style={[styles.optionButton, showTranslation && styles.optionButtonActive]}
            onPress={() => setShowTranslation(!showTranslation)}
          >
            <Ionicons
              name="language"
              size={20}
              color={showTranslation ? '#2196F3' : '#666'}
            />
            <Text style={[styles.optionText, showTranslation && styles.optionTextActive]}>
              中英对照
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.optionButton, loopSentence && styles.optionButtonActive]}
            onPress={() => setLoopSentence(!loopSentence)}
          >
            <Ionicons
              name="repeat"
              size={20}
              color={loopSentence ? '#2196F3' : '#666'}
            />
            <Text style={[styles.optionText, loopSentence && styles.optionTextActive]}>
              单句循环
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.optionButton}
            onPress={changeSpeed}
          >
            <Ionicons name="speedometer" size={20} color="#666" />
            <Text style={styles.optionText}>{playbackSpeed}x</Text>
          </TouchableOpacity>
        </View>

        {/* 播放控制 */}
        <View style={styles.playbackControls}>
          <TouchableOpacity
            style={styles.controlButton}
            onPress={previousSentence}
            disabled={currentSentenceIndex === 0}
          >
            <Ionicons
              name="play-skip-back"
              size={32}
              color={currentSentenceIndex === 0 ? '#ccc' : '#333'}
            />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.playButton}
            onPress={togglePlayPause}
          >
            <Ionicons
              name={isPlaying ? 'pause' : 'play'}
              size={48}
              color="#fff"
            />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.controlButton}
            onPress={nextSentence}
            disabled={currentSentenceIndex === lesson.sentences.length - 1}
          >
            <Ionicons
              name="play-skip-forward"
              size={32}
              color={
                currentSentenceIndex === lesson.sentences.length - 1
                  ? '#ccc'
                  : '#333'
              }
            />
          </TouchableOpacity>
        </View>

        {/* 进度条 */}
        <View style={styles.progressContainer}>
          <Text style={styles.progressText}>
            {currentSentenceIndex + 1} / {lesson.sentences.length}
          </Text>
          <View style={styles.progressBar}>
            <View
              style={[
                styles.progressFill,
                {
                  width: `${
                    ((currentSentenceIndex + 1) / lesson.sentences.length) * 100
                  }%`,
                },
              ]}
            />
          </View>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#fff',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  lessonTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  lessonTitleCn: {
    fontSize: 16,
    color: '#666',
    marginTop: 4,
  },
  playCountText: {
    fontSize: 14,
    color: '#2196F3',
    marginTop: 8,
  },
  contentArea: {
    flex: 1,
    padding: 12,
  },
  sentenceCard: {
    backgroundColor: '#fff',
    padding: 16,
    marginBottom: 12,
    borderRadius: 8,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  sentenceCardActive: {
    borderColor: '#2196F3',
    backgroundColor: '#E3F2FD',
  },
  sentenceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  sentenceNumber: {
    fontSize: 12,
    color: '#999',
    fontWeight: '600',
  },
  sentencePlayCount: {
    fontSize: 12,
    color: '#2196F3',
  },
  sentenceEn: {
    fontSize: 16,
    color: '#333',
    marginBottom: 8,
    lineHeight: 24,
  },
  sentenceCn: {
    fontSize: 14,
    color: '#666',
    lineHeight: 22,
  },
  controlPanel: {
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
    paddingVertical: 16,
    paddingHorizontal: 20,
  },
  optionsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 20,
  },
  optionButton: {
    alignItems: 'center',
    padding: 8,
    borderRadius: 8,
  },
  optionButtonActive: {
    backgroundColor: '#E3F2FD',
  },
  optionText: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  optionTextActive: {
    color: '#2196F3',
    fontWeight: '600',
  },
  playbackControls: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  controlButton: {
    padding: 12,
  },
  playButton: {
    backgroundColor: '#2196F3',
    width: 72,
    height: 72,
    borderRadius: 36,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 32,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
  },
  progressContainer: {
    alignItems: 'center',
  },
  progressText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  progressBar: {
    width: '100%',
    height: 4,
    backgroundColor: '#e0e0e0',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#2196F3',
  },
});
